import os

import numpy as np
import pytest

from app.embeddings import MiniLM


@pytest.fixture(scope="module")
def model():
    if os.environ.get("RUN_MODEL_TESTS") != "1":
        pytest.skip("Set RUN_MODEL_TESTS=1 after downloading pinned model")
    return MiniLM()


@pytest.mark.model
def test_real_minilm_normalization_similarity_and_limit(model):
    vectors = np.array(model.encode([
        "Database connection pools reuse connections.",
        "Pooling reuses database sessions.",
        "Sunflowers grow in the garden.",
    ]))
    assert vectors.shape == (3, 384)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)
    assert vectors[0] @ vectors[1] > vectors[0] @ vectors[2]
    assert model.max_tokens == 256
    assert model.special_tokens == 2
    with pytest.raises(ValueError, match="chunk first"):
        model.encode(["database " * 300])
    assert model.encode(["Oracle supports Unicode: 数据库, café."])


@pytest.mark.oracle
def test_real_oracle_rollback_and_ranking(model):
    if os.environ.get("RUN_ORACLE_TESTS") != "1":
        pytest.skip("Set RUN_ORACLE_TESTS=1 with configured dedicated Oracle schema")
    from app.config import OracleSettings
    from app.oracle import connect, vector_smoke
    with connect(OracleSettings.from_env()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            before = cursor.fetchone()[0]
        assert vector_smoke(connection, model)["nearest_chunk"] == 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            assert cursor.fetchone()[0] == before
