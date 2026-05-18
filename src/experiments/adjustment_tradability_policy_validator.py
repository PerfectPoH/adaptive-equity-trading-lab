from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "adjustment_tradability_policy_manifest.json",
    "adjustment_tradability_policy.csv",
    "policy_stop_conditions.csv",
    "policy_enforcement_matrix.csv",
    "adjustment_tradability_policy_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "purpose",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_policy_tables",
]

REQUIRED_POLICY_AREAS = [
    "price_adjustment",
    "corporate_actions",
    "halt_tradability",
    "PIT_universe",
    "licensing_retention",
    "provider_quality_warnings",
]

REQUIRED_STOP_CONDITIONS = [
    "adjustment_policy_unknown_and_performance_requested",
    "corporate_action_source_missing_for_adjusted_claim",
    "halt_tradability_unknown_for_small_cap_execution",
    "PIT_universe_missing_for_universe_claim",
    "raw_retention_required_without_license",
    "provider_quality_warning_ignored",
]

REQUIRED_RESEARCH_STAGES = [
    "data_quality_diagnostic",
    "fixed_signal_replay",
    "new_signal_research",
    "portfolio_backtest",
    "OOS",
    "paper_live",
]


def validate_adjustment_tradability_policy(policy_dir: str | Path) -> dict[str, Any]:
    path = Path(policy_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "policy_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "adjustment_tradability_policy_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    policy = _read_csv(path / "adjustment_tradability_policy.csv", checks, "csv_readable:adjustment_tradability_policy.csv")
    stop_conditions = _read_csv(path / "policy_stop_conditions.csv", checks, "csv_readable:policy_stop_conditions.csv")
    enforcement = _read_csv(path / "policy_enforcement_matrix.csv", checks, "csv_readable:policy_enforcement_matrix.csv")
    _read_text_file(path / "adjustment_tradability_policy_summary.md", checks, "markdown_readable:adjustment_tradability_policy_summary.md")

    if policy is not None:
        _validate_policy_table(policy, checks)
    if stop_conditions is not None:
        _validate_stop_conditions(stop_conditions, checks)
    if enforcement is not None:
        _validate_enforcement(enforcement, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_adjustment_tradability_policy(args.policy_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate adjustment and tradability policy artifacts.")
    parser.add_argument("--policy-dir", required=True, help="Adjustment/tradability policy artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_policy_tables"), list) and bool(manifest.get("required_policy_tables"))
    no_provider_query_ok = manifest.get("no_provider_query") is True
    no_backtest_ok = manifest.get("no_backtest") is True
    no_strategy_promotion_ok = manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_policy_tables_ok={tables_ok}")
    _add_check(
        checks,
        "manifest_no_execution_flags",
        no_provider_query_ok and no_backtest_ok and no_strategy_promotion_ok,
        f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}",
    )


def _validate_policy_table(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"policy_area", "current_status", "allowed_for_diagnostics", "allowed_for_performance", "required_before_performance", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "policy_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    areas = {str(value) for value in frame["policy_area"].dropna().tolist()}
    missing_areas = [area for area in REQUIRED_POLICY_AREAS if area not in areas]
    _add_check(checks, "policy_required_areas", not missing_areas, f"missing={missing_areas}")
    performance_values = frame["allowed_for_performance"].astype(str).str.lower().tolist()
    performance_not_silently_allowed = all(value in {"no", "conditional"} for value in performance_values)
    _add_check(checks, "policy_performance_not_silently_allowed", performance_not_silently_allowed, f"allowed_for_performance={performance_values}")


def _validate_stop_conditions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"stop_condition", "severity", "blocked_work", "resolution_required"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "stop_conditions_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    stops = {str(value) for value in frame["stop_condition"].dropna().tolist()}
    missing_stops = [stop for stop in REQUIRED_STOP_CONDITIONS if stop not in stops]
    critical_count = int(frame["severity"].astype(str).str.lower().eq("critical").sum())
    _add_check(checks, "stop_conditions_required_items", not missing_stops, f"missing={missing_stops}")
    _add_check(checks, "stop_conditions_have_critical_items", critical_count >= 5, f"critical_count={critical_count}")


def _validate_enforcement(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"research_stage", "policy_required", "minimum_policy_status", "promotion_allowed"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "enforcement_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    stages = {str(value) for value in frame["research_stage"].dropna().tolist()}
    missing_stages = [stage for stage in REQUIRED_RESEARCH_STAGES if stage not in stages]
    all_required = frame["policy_required"].astype(str).str.lower().eq("yes").all()
    promotion_values = frame["promotion_allowed"].astype(str).str.lower().tolist()
    promotion_not_silently_allowed = all(value in {"no", "no_until_separate_promotion_gate", "conditional"} for value in promotion_values)
    _add_check(checks, "enforcement_required_stages", not missing_stages, f"missing={missing_stages}")
    _add_check(checks, "enforcement_all_policy_required", bool(all_required), f"all_policy_required={bool(all_required)}")
    _add_check(checks, "enforcement_promotion_not_silently_allowed", promotion_not_silently_allowed, f"promotion_allowed={promotion_values}")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, not frame.empty and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text_file(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "policy_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
