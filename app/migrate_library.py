"""Run the repeatable additive library migration as the schema owner."""
from pathlib import Path

import oracledb

from app.config import OracleSettings
from app.oracle import connect


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "sql" / "002_library.sql"
    try:
        with connect(OracleSettings.from_env()) as connection, connection.cursor() as cursor:
            cursor.execute(path.read_text(encoding="utf-8").rsplit("/", 1)[0].strip())
            cursor.execute("SELECT d.document_type, c.page_number FROM documents d, document_chunks c WHERE 1=0")
    except (oracledb.Error, OSError, ValueError) as error:
        code = getattr(error.args[0], "full_code", type(error).__name__) if error.args else type(error).__name__
        print(f"Library migration failed ({code})")
        return 1
    print("Library schema verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
