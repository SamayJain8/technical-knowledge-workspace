"""Local Oracle configuration; never include values in errors or repr."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, repr=False)
class OracleSettings:
    user: str = field(repr=False)
    password: str = field(repr=False)
    dsn: str = field(repr=False)
    wallet_dir: str | None = field(default=None, repr=False)
    wallet_password: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "OracleSettings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        missing = [
            name for name in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
            if not os.environ.get(name, "").strip()
        ]
        if missing:
            raise ConfigurationError("Configure locally: " + ", ".join(missing))
        dsn = os.environ["ORACLE_DSN"].strip()
        wallet_dir = os.environ.get("ORACLE_WALLET_DIR") or None
        # Aliases require a local wallet/tnsnames directory; the parsed connection
        # parameters are checked again by connect() before any network operation.
        if wallet_dir and not Path(wallet_dir).is_dir():
            raise ConfigurationError("ORACLE_WALLET_DIR must be an existing directory")
        return cls(
            user=os.environ["ORACLE_USER"].strip(),
            password=os.environ["ORACLE_PASSWORD"],
            dsn=dsn,
            wallet_dir=wallet_dir,
            wallet_password=os.environ.get("ORACLE_WALLET_PASSWORD") or None,
        )
