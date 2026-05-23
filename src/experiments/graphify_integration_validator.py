"""Validation and dry-run planning for the Graphify local tooling gate."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_ALLOWED_SCOPES = {
    "src",
    "tests",
    "vault/04-Documentazione/Reports",
}

REQUIRED_BLOCKED_PATHS = {
    ".env",
    ".git",
    ".venv",
    ".venv-lab",
    "experiments/provider_aware_research/data_inputs",
    "experiments/provider_aware_research/execution_outputs",
}

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "market_data_download",
    "strategy_backtest",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "scan_secrets",
}

APPROVED_STATUSES = {"SPEC_ONLY_LOCAL_TOOLING_NOT_RUN"}


@dataclass(frozen=True)
class ValidationResult:
    """Structured result for Graphify integration artifact checks."""

    status: str
    reasons: tuple[str, ...]
    artifact_id: str | None = None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_first_column(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if column not in (reader.fieldnames or []):
            raise ValueError(f"{path} missing required column {column!r}")
        return {row[column].strip() for row in reader if row.get(column)}


def _missing(required: Iterable[str], observed: Iterable[str]) -> tuple[str, ...]:
    observed_set = set(observed)
    return tuple(sorted(item for item in required if item not in observed_set))


def validate_graphify_integration(spec_dir: str | Path) -> ValidationResult:
    """Validate the Graphify integration gate artifact."""

    root = Path(spec_dir)
    reasons: list[str] = []

    manifest_path = root / "graphify_integration_manifest.json"
    allowed_path = root / "allowed_scopes.csv"
    blocked_paths_path = root / "blocked_paths.csv"
    blocked_actions_path = root / "blocked_actions.csv"

    for path in (manifest_path, allowed_path, blocked_paths_path, blocked_actions_path):
        if not path.exists():
            reasons.append(f"missing required file: {path.name}")

    if reasons:
        return ValidationResult("FAIL", tuple(reasons))

    manifest = _read_json(manifest_path)
    artifact_id = manifest.get("artifact_id")

    if artifact_id != "GRAPHIFY-INTEGRATION-001":
        reasons.append("manifest artifact_id must be GRAPHIFY-INTEGRATION-001")
    if manifest.get("status") not in APPROVED_STATUSES:
        reasons.append("manifest status is not approved for local tooling planning")
    if manifest.get("execution_performed") is not False:
        reasons.append("manifest must record execution_performed=false")
    if manifest.get("raw_graph_outputs_retained") is not False:
        reasons.append("manifest must record raw_graph_outputs_retained=false before first run")
    if manifest.get("package_name") != "graphifyy":
        reasons.append("manifest package_name must be graphifyy")
    if manifest.get("cli_command") != "graphify":
        reasons.append("manifest cli_command must be graphify")

    allowed_scopes = _read_first_column(allowed_path, "scope")
    missing_scopes = _missing(REQUIRED_ALLOWED_SCOPES, allowed_scopes)
    if missing_scopes:
        reasons.append(f"missing required allowed scopes: {', '.join(missing_scopes)}")

    blocked_paths = _read_first_column(blocked_paths_path, "path")
    missing_paths = _missing(REQUIRED_BLOCKED_PATHS, blocked_paths)
    if missing_paths:
        reasons.append(f"missing required blocked paths: {', '.join(missing_paths)}")

    blocked_actions = _read_first_column(blocked_actions_path, "action")
    missing_actions = _missing(REQUIRED_BLOCKED_ACTIONS, blocked_actions)
    if missing_actions:
        reasons.append(f"missing required blocked actions: {', '.join(missing_actions)}")

    forbidden_use = set(manifest.get("forbidden_use", []))
    missing_forbidden = _missing(REQUIRED_BLOCKED_ACTIONS, forbidden_use)
    if missing_forbidden:
        reasons.append(f"manifest missing forbidden_use entries: {', '.join(missing_forbidden)}")

    return ValidationResult("FAIL" if reasons else "PASS", tuple(reasons), artifact_id=artifact_id)


def _normalize_scope(value: str | Path) -> str:
    return Path(value).as_posix().rstrip("/")


def build_graphify_dry_run_plan(
    spec_dir: str | Path,
    target_scope: str | Path,
    output_dir: str | Path,
) -> dict:
    """Build a non-executing Graphify command plan after validating the gate."""

    validation = validate_graphify_integration(spec_dir)
    target = _normalize_scope(target_scope)
    output = _normalize_scope(output_dir)

    if not validation.passed:
        return {
            "status": "BLOCKED",
            "graphify_execution_performed": False,
            "reasons": list(validation.reasons),
        }

    allowed_scopes = _read_first_column(Path(spec_dir) / "allowed_scopes.csv", "scope")
    blocked_paths = _read_first_column(Path(spec_dir) / "blocked_paths.csv", "path")

    reasons: list[str] = []
    if target not in allowed_scopes:
        reasons.append(f"target scope is not approved: {target}")
    if target in blocked_paths:
        reasons.append(f"target scope is explicitly blocked: {target}")

    output_path = Path(output)
    if output_path.name == "graphify-out":
        reasons.append("output_dir must be a bounded parent directory, not graphify-out itself")

    if reasons:
        return {
            "status": "BLOCKED",
            "graphify_execution_performed": False,
            "reasons": reasons,
        }

    return {
        "status": "DRY_RUN_READY",
        "artifact_id": validation.artifact_id,
        "graphify_execution_performed": False,
        "target_scope": target,
        "output_dir": output,
        "command": ["graphify", target],
        "expected_outputs": [
            f"{output}/graphify-out/graph.html",
            f"{output}/graphify-out/GRAPH_REPORT.md",
            f"{output}/graphify-out/graph.json",
        ],
        "notes": [
            "No provider query is authorized.",
            "No market data download is authorized.",
            "No backtest or strategy promotion is authorized.",
            "A real scan must be committed as a separate run after this gate.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and dry-plan Graphify local tooling.")
    parser.add_argument(
        "--spec-dir",
        default="experiments/tooling/graphify_integration_20260523",
        help="Graphify integration artifact directory.",
    )
    parser.add_argument("--target-scope", default="src", help="Approved local scope to graph.")
    parser.add_argument(
        "--output-dir",
        default="experiments/tooling/graphify_runs/graphify_src_20260523",
        help="Bounded output parent directory for a future Graphify run.",
    )
    args = parser.parse_args(argv)

    plan = build_graphify_dry_run_plan(args.spec_dir, args.target_scope, args.output_dir)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if plan["status"] in {"DRY_RUN_READY", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
