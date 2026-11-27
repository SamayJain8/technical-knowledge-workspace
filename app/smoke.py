"""Run M1 checks without provisioning services or calling a paid LLM."""

import argparse
import json
import re
import sys

from app.config import ConfigurationError, OracleSettings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=["model", "oracle"])
    parser.add_argument("--download", action="store_true", help="Download pinned public MiniLM weights")
    parser.add_argument("--init-schema", action="store_true", help="Create project tables (Oracle DDL commits)")
    args = parser.parse_args()
    if args.init_schema and args.target != "oracle":
        parser.error("--init-schema requires oracle target")
    try:
        # Fail on missing configuration before loading a model or touching the network.
        settings = OracleSettings.from_env() if args.target == "oracle" else None
        from app.embeddings import MiniLM
        model = MiniLM(allow_download=args.download)
        vectors = model.encode(["Database connection pooling reuses sessions."])
        report = {"model_fingerprint": model.fingerprint, "dimensions": len(vectors[0]),
                  "max_tokens": model.max_tokens, "special_tokens": model.special_tokens}
        if settings:
            from app.oracle import connect, initialize_schema, vector_smoke
            with connect(settings) as connection:
                if args.init_schema:
                    initialize_schema(connection)
                report["oracle"] = vector_smoke(connection, model)
        print(json.dumps(report, sort_keys=True))
        return 0
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    except Exception as error:
        # Driver/model errors may contain credentials, connect descriptors or tokens.
        code = getattr(error.args[0], "full_code", "") if error.args else ""
        label = code if isinstance(code, str) and re.fullmatch(r"[A-Z]{2,4}-\d{4,5}", code) else type(error).__name__
        print(f"Smoke check failed ({label}); verify model cache/network, TLS configuration, schema and service availability. No live success verified.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
