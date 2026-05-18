from __future__ import annotations

import argparse
import json
import os
from typing import Any

DEFAULT_REQUIRED_ENV_VARS = ("DATABENTO_API_KEY", "POLYGON_API_KEY")


def inspect_credential_environment(required_env_vars: tuple[str, ...] = DEFAULT_REQUIRED_ENV_VARS) -> dict[str, Any]:
    checks = []
    for name in required_env_vars:
        value = os.environ.get(name)
        checks.append({
            "name": name,
            "present": bool(value),
            "value_disclosed": False,
        })
    missing = sorted(item["name"] for item in checks if not item["present"])
    return {
        "status": "pass" if not missing else "blocked",
        "provider_query_performed": False,
        "network_call_performed": False,
        "secret_values_disclosed": False,
        "required_env_vars": list(required_env_vars),
        "missing_env_vars": missing,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    required = tuple(args.required_env_var) if args.required_env_var else DEFAULT_REQUIRED_ENV_VARS
    report = inspect_credential_environment(required)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect provider credential environment without provider queries.")
    parser.add_argument("--required-env-var", action="append", default=[], help="Required environment variable name to check for presence only.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
