from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

DEFAULT_REQUIRED_ENV_VARS = ("DATABENTO_API_KEY", "POLYGON_API_KEY")


def inspect_credential_environment(
    required_env_vars: tuple[str, ...] = DEFAULT_REQUIRED_ENV_VARS,
    env_file: str | Path = ".env",
    source: str = "auto",
) -> dict[str, Any]:
    env_path = Path(env_file)
    file_values = dotenv_values(env_path) if env_path.exists() else {}
    checks = []
    for name in required_env_vars:
        environment_value = os.environ.get(name, "")
        file_value = str(file_values.get(name) or "")
        selected_source = _select_source(source, bool(environment_value), bool(file_value))
        present = selected_source in {"environment", "env-file"}
        checks.append({
            "name": name,
            "present": present,
            "source": selected_source,
            "environment_present": bool(environment_value),
            "env_file_present": bool(file_value),
            "value_disclosed": False,
        })
    missing = sorted(item["name"] for item in checks if not item["present"])
    return {
        "status": "pass" if not missing else "blocked",
        "provider_query_performed": False,
        "network_call_performed": False,
        "secret_values_disclosed": False,
        "env_file": str(env_path),
        "env_file_exists": env_path.exists(),
        "source": source,
        "required_env_vars": list(required_env_vars),
        "missing_env_vars": missing,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    required = tuple(args.required_env_var) if args.required_env_var else DEFAULT_REQUIRED_ENV_VARS
    report = inspect_credential_environment(required, env_file=args.env_file, source=args.source)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect provider credential environment without provider queries.")
    parser.add_argument("--required-env-var", action="append", default=[], help="Required environment variable name to check for presence only.")
    parser.add_argument("--env-file", default=".env", help="Env file to inspect for key presence only.")
    parser.add_argument("--source", choices=["auto", "environment", "env-file"], default="auto", help="Credential source to inspect.")
    return parser


def _select_source(source: str, environment_present: bool, env_file_present: bool) -> str:
    if source == "environment":
        return "environment" if environment_present else "missing"
    if source == "env-file":
        return "env-file" if env_file_present else "missing"
    if environment_present:
        return "environment"
    if env_file_present:
        return "env-file"
    return "missing"


if __name__ == "__main__":
    raise SystemExit(main())
