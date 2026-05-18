from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "provider_coverage_contract_manifest.json",
    "coverage_contract_schema.csv",
    "coverage_contract_template.csv",
    "coverage_validation_checklist.csv",
    "coverage_contract_enforcement_policy.csv",
    "provider_coverage_contract_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "purpose",
    "no_provider_query",
    "no_backtest",
    "required_for",
    "minimum_contract_tables",
]

REQUIRED_CONTRACT_FIELDS = [
    "contract_id",
    "provider_combo",
    "dataset_or_endpoint",
    "coverage_start",
    "coverage_end",
    "symbol_scope",
    "missingness_policy",
    "adjustment_policy",
    "corporate_action_policy",
    "halt_tradability_policy",
    "PIT_universe_policy",
    "licensing_retention_policy",
    "provider_quality_warnings",
    "stop_conditions",
    "approved_uses",
    "blocked_uses",
]

REQUIRED_CHECKLIST_CHECKS = [
    "coverage_dates_declared",
    "symbol_scope_frozen",
    "missingness_policy_declared",
    "adjustment_policy_declared",
    "corporate_action_policy_declared",
    "halt_tradability_policy_declared",
    "PIT_universe_policy_declared",
    "licensing_policy_declared",
    "provider_warning_capture",
    "stop_conditions_declared",
]

REQUIRED_ENFORCEMENT_USE_CASES = [
    "data_quality_audit",
    "fixed_signal_replay",
    "new_signal_research",
    "portfolio_backtest",
    "OOS",
    "paper_live_trading",
]

BLOCKED_TEMPLATE_VALUES = {"", "unknown", "tbd", "todo", "n/a"}


def validate_provider_coverage_contract(contract_dir: str | Path) -> dict[str, Any]:
    path = Path(contract_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "contract_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "provider_coverage_contract_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    schema = _read_csv(path / "coverage_contract_schema.csv", checks, "csv_readable:coverage_contract_schema.csv")
    template = _read_csv(path / "coverage_contract_template.csv", checks, "csv_readable:coverage_contract_template.csv")
    checklist = _read_csv(path / "coverage_validation_checklist.csv", checks, "csv_readable:coverage_validation_checklist.csv")
    enforcement = _read_csv(path / "coverage_contract_enforcement_policy.csv", checks, "csv_readable:coverage_contract_enforcement_policy.csv")
    _read_text_file(path / "provider_coverage_contract_summary.md", checks, "markdown_readable:provider_coverage_contract_summary.md")

    if schema is not None:
        _validate_schema(schema, checks)
    if template is not None:
        _validate_template(template, checks)
    if checklist is not None:
        _validate_checklist(checklist, checks)
    if enforcement is not None:
        _validate_enforcement(enforcement, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_provider_coverage_contract(args.contract_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate provider coverage contract artifacts.")
    parser.add_argument("--contract-dir", required=True, help="Provider coverage contract artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    required_for_ok = isinstance(manifest.get("required_for"), list) and bool(manifest.get("required_for"))
    tables_ok = isinstance(manifest.get("minimum_contract_tables"), list) and bool(manifest.get("minimum_contract_tables"))
    no_provider_query_ok = manifest.get("no_provider_query") is True
    no_backtest_ok = manifest.get("no_backtest") is True
    _add_check(
        checks,
        "manifest_required_fields",
        not missing and required_for_ok and tables_ok,
        f"missing={missing}; required_for_ok={required_for_ok}; minimum_contract_tables_ok={tables_ok}",
    )
    _add_check(
        checks,
        "manifest_no_execution_flags",
        no_provider_query_ok and no_backtest_ok,
        f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}",
    )


def _validate_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "required", "allowed_or_format", "description"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "schema_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = {str(value) for value in frame["field"].dropna().tolist()}
    missing_fields = [field for field in REQUIRED_CONTRACT_FIELDS if field not in fields]
    _add_check(checks, "schema_required_contract_fields", not missing_fields, f"missing={missing_fields}")


def _validate_template(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing_columns = [field for field in REQUIRED_CONTRACT_FIELDS if field not in frame.columns]
    _add_check(checks, "template_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    _add_check(checks, "template_single_contract_row", len(frame) == 1, f"rows={len(frame)}")
    if frame.empty:
        return
    row = frame.iloc[0]
    blocked_values = []
    for field in REQUIRED_CONTRACT_FIELDS:
        value = str(row.get(field, "")).strip().lower()
        if value in BLOCKED_TEMPLATE_VALUES:
            blocked_values.append(field)
    _add_check(checks, "template_required_values_populated", not blocked_values, f"blocked_or_empty={blocked_values}")


def _validate_checklist(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"check", "severity", "pass_condition", "failure_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "checklist_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    checks_present = {str(value) for value in frame["check"].dropna().tolist()}
    missing_checks = [check for check in REQUIRED_CHECKLIST_CHECKS if check not in checks_present]
    _add_check(checks, "checklist_required_checks", not missing_checks, f"missing={missing_checks}")


def _validate_enforcement(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"use_case", "contract_required", "minimum_status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "enforcement_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    use_cases = {str(value) for value in frame["use_case"].dropna().tolist()}
    missing_use_cases = [use_case for use_case in REQUIRED_ENFORCEMENT_USE_CASES if use_case not in use_cases]
    all_required = frame["contract_required"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "enforcement_required_use_cases", not missing_use_cases, f"missing={missing_use_cases}")
    _add_check(checks, "enforcement_all_contract_required", bool(all_required), f"all_contract_required={bool(all_required)}")


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
        "contract_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
