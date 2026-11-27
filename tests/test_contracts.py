import math

import pytest

from app.config import ConfigurationError, OracleSettings
from app.embeddings import oracle_vector, validate_texts


@pytest.mark.parametrize("texts", [[], "abc", [""], ["  "], [None], ["x" * 32001], ["x"] * 33])
def test_invalid_embedding_input(texts):
    with pytest.raises(ValueError):
        validate_texts(texts)


@pytest.mark.parametrize("vector", [[1.0] * 383, [0.0] * 384, [math.nan] * 384, [math.inf] * 384, [1.0] * 384])
def test_reject_invalid_vectors(vector):
    with pytest.raises(ValueError):
        oracle_vector(vector)


def test_float32_transport():
    vector = oracle_vector([1.0] + [0.0] * 383)
    assert vector.typecode == "f"
    assert len(vector) == 384


def test_missing_configuration_has_no_values(monkeypatch):
    monkeypatch.setattr("app.config.load_dotenv", lambda *args, **kwargs: None)
    for name in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigurationError, match="ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN"):
        OracleSettings.from_env()


def test_config_repr_redacts_secrets():
    settings = OracleSettings("private-user", "private-password", "private-host")
    assert "private" not in repr(settings)


def test_reject_plaintext_oracle_before_connect():
    from app.oracle import connect
    with pytest.raises(ConfigurationError, match="TLS"):
        connect(OracleSettings("user", "secret", "tcp://localhost:1521/service"))


def test_reject_mixed_protocols_before_connect():
    from app.oracle import connect
    dsn = "(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCPS)(HOST=localhost)(PORT=1522))(ADDRESS=(PROTOCOL=TCP)(HOST=localhost)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=test)))"
    with pytest.raises(ConfigurationError, match="TLS"):
        connect(OracleSettings("user", "secret", dsn))


def test_smoke_rejects_autocommit_before_writes():
    from types import SimpleNamespace
    from app.oracle import vector_smoke
    with pytest.raises(ValueError, match="autocommit"):
        vector_smoke(SimpleNamespace(autocommit=True), None)


def test_smoke_rolls_back_when_insert_fails():
    from unittest.mock import MagicMock
    from app.oracle import vector_smoke
    connection = MagicMock(autocommit=False)
    connection.cursor.return_value.__enter__.return_value.execute.side_effect = RuntimeError("insert failed")
    model = MagicMock()
    model.encode.return_value = [oracle_vector([1.0] + [0.0] * 383)] * 2
    with pytest.raises(RuntimeError, match="insert failed"):
        vector_smoke(connection, model)
    connection.rollback.assert_called_once()
