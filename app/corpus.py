"""Load a bounded local JSONL corpus and prepare stable, attributed chunks."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from app.embeddings import MiniLM

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "database_operations.jsonl"


@dataclass(frozen=True)
class Document:
    title: str
    source_url: str
    provenance: str
    license: str
    text: str


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_documents(path: Path) -> list[Document]:
    with path.open("rb") as source:
        raw = source.read(262145)
    if len(raw) > 262144:
        raise ValueError("Corpus exceeds 256 KiB")

    documents = []
    urls, hashes = set(), set()
    limits = {"title": 512, "source_url": 2048, "provenance": 1800,
              "license": 100, "text": 32000}
    for number, line in enumerate(raw.decode("utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or row.keys() != limits.keys():
                raise ValueError
            for key, limit in limits.items():
                value = row[key]
                if not isinstance(value, str) or "\x00" in value:
                    raise ValueError
                value = "\n".join(part.rstrip() for part in value.splitlines()).strip()
                if not value or len(value.encode("utf-8")) > limit:
                    raise ValueError
                row[key] = value
            url = urlsplit(row["source_url"])
            if (url.scheme != "https" or not url.hostname or url.username
                    or url.password or any(char.isspace() for char in row["source_url"])):
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid corpus metadata or text at line {number}") from None
        content_hash = digest(" ".join(row["text"].split()))
        if row["source_url"] in urls:
            raise ValueError(f"Duplicate source URL at line {number}")
        urls.add(row["source_url"])
        if content_hash not in hashes:
            documents.append(Document(**row))
            hashes.add(content_hash)
        if len(urls) > 32:
            raise ValueError("Corpus exceeds 32 sources")
    if not documents:
        raise ValueError("Corpus is empty")
    return documents


def chunk_text(text: str, model: MiniLM) -> list[str]:
    tokenizer = model.model.tokenizer
    offsets = tokenizer(text, add_special_tokens=False, truncation=False,
                        return_offsets_mapping=True, verbose=False)["offset_mapping"]
    size = min(200, model.max_tokens - model.special_tokens)
    if not offsets:
        raise ValueError("Document contains no model tokens")
    chunks = []
    start = 0
    while start < len(offsets):
        end = min(start + size, len(offsets))
        while end > start:
            part = text[offsets[start][0]:offsets[end - 1][1]].strip()
            if part and len(tokenizer.encode(part, truncation=False)) <= model.max_tokens:
                break
            end -= 1
        if end == start:
            raise ValueError("Could not chunk document within model token limit")
        chunks.append(part)
        if len(chunks) > 256:
            raise ValueError("Document exceeds 256 chunks")
        if end == len(offsets):
            break
        start = max(start + 1, end - 30)
    return chunks
