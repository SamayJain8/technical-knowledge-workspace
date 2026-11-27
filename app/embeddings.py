"""One pinned CPU model; reject oversized input instead of silent truncation."""

import hashlib
import json
import os
from array import array
from pathlib import Path
from typing import Sequence

import numpy as np

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
DIMENSIONS = 384
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "huggingface"


def validate_texts(texts: Sequence[str], *, maximum_batch: int = 32) -> None:
    if isinstance(texts, str) or not 1 <= len(texts) <= maximum_batch:
        raise ValueError(f"Expected 1 to {maximum_batch} texts")
    if any(not isinstance(text, str) or not text.strip() or len(text) > 32000 for text in texts):
        raise ValueError("Texts must be nonempty strings of at most 32000 characters")


def oracle_vector(values: Sequence[float]) -> array:
    vector = np.asarray(values, dtype=np.float32)
    if vector.shape != (DIMENSIONS,) or not np.isfinite(vector).all():
        raise ValueError("Expected a finite 384-dimensional vector")
    if not np.isclose(np.linalg.norm(vector), 1.0, atol=1e-5):
        raise ValueError("Expected a normalized vector")
    return array("f", vector)


class MiniLM:
    def __init__(self, *, allow_download: bool = False) -> None:
        # Avoid sending ambient Hugging Face credentials for this public model.
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        from sentence_transformers import SentenceTransformer
        import torch

        torch.set_num_threads(2)
        self.model = SentenceTransformer(
            MODEL_ID,
            revision=MODEL_REVISION,
            device="cpu",
            cache_folder=str(CACHE_DIR),
            local_files_only=not allow_download,
            trust_remote_code=False,
            token=False,
            model_kwargs={"use_safetensors": True},
        )
        if self.model.get_sentence_embedding_dimension() != DIMENSIONS:
            raise ValueError("Unexpected embedding dimension")
        self.max_tokens = min(self.model.max_seq_length, self.model.tokenizer.model_max_length)
        if not 2 < self.max_tokens <= 512:
            raise ValueError("Unexpected model token limit")
        self.special_tokens = self.model.tokenizer.num_special_tokens_to_add(pair=False)
        # This fingerprint travels with every stored vector. Same dimension alone
        # does not prove compatibility; revision and preprocessing must also match.
        contract = {
            "model": MODEL_ID, "revision": MODEL_REVISION,
            "dimensions": DIMENSIONS, "normalize": True, "dtype": "float32",
            "preprocessing": "identity-v1", "max_tokens": self.max_tokens,
        }
        self.fingerprint = hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()

    def encode(self, texts: Sequence[str]) -> list[array]:
        validate_texts(texts)
        lengths = [len(self.model.tokenizer.encode(text, truncation=False, verbose=False)) for text in texts]
        if any(length > self.max_tokens for length in lengths):
            raise ValueError(f"Input exceeds model limit of {self.max_tokens} tokens; chunk first")
        vectors = self.model.encode(
            list(texts), batch_size=8, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )
        return [oracle_vector(vector) for vector in vectors]
