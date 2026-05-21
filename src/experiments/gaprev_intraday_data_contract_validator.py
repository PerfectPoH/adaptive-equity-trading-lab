from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "intraday_data_contract_manifest.json",
    "intraday_coverage_requirements.csv",
    "bar_schema_requirements.csv",
    "calendar_and_session_policy.csv",
    "execution_cost_proxy_requirements.csv",
    "blocked_actions.csv",
]

REQUIRED_BAR_FIELDS = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
REQUIRED_CALENDAR_ITEMS = {
    "session_timezone",
    "regular_open",
    "regular_close",
    "half_days",
    "holidays",
    "prior_close_mapping",
    "open_mapping",
    "late_open_or_halt",
}
REQUIRED_COST_COMPONENTS = {
    "spread_proxy",
    "slippage_model",
    "market_impact_model",
    "commission_model",
    "max_participation_rate",
    "gap_open_fill_policy",
    "no_gross_only_metrics",
}
REQUIRED_BLOCKED_ACTIONS = {
    "select_provider",
    "provider_query",
    "download_intraday_data",
    "implement_extractor",
    "build_intraday_bars",
    "compute_vwap_signals",
    "execute_backtest",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_gaprev_intraday_data_contract(contract_dir: str | Path) -> dict[str, Any]:
    path = Path(contract_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "contract_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "intraday_data_contract_manifest.json", checks, "manifest_json")
    coverage = _read_csv(path / "intraday_coverage_requirements.csv", checks, "csv_readable:intraday_coverage_requirements.csv")
    schema = _read_csv(path / "bar_schema_requirements.csv", checks, "csv_readable:bar_schema_requirements.csv")
    calendar = _read_csv(path / "calendar_and_session_policy.csv", checks, "csv_readable:calendar_and_session_policy.csv")
    costs = _read_csv(path / "execution_cost_proxy_requirements.csv", checks, "csv_readable:execution_cost_proxy_requirements.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    _read_text(path / "README.md", checks, "markdown_readable:README.md")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if coverage is not None:
        _validate_coverage(coverage, checks)
    if schema is not None:
        _validate_schema(schema, checks)
    if calendar is not None:
        _validate_calendar(calendar, checks)
    if costs is not None:
        _validate_costs(costs, checks)
    if blocked is not None:
        _validate_blocked(blocked, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_gaprev_intraday_data_contract(args.contract_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate GAPREV intraday data-contract gate.")
    parser.add_argument("--contract-dir", required=True)
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    _add_check(checks, "manifest_status_spec_only", manifest.get("status") == "SPEC_ONLY_NOT_QUERIED", f"status={manifest.get('status')}")
    _add_check(checks, "manifest_identity", manifest.get("gate_id") == "GAPREV-INTRADAY-DATA-CONTRACT-001" and manifest.get("trial_id") == "TRIAL-GAPREV-001", f"gate={manifest.get('gate_id')}; trial={manifest.get('trial_id')}")
    safe = (
        manifest.get("provider_selected") is False
        and manifest.get("provider_query_performed") is False
        and manifest.get("network_call_performed") is False
        and manifest.get("market_data_downloaded") is False
        and manifest.get("extractor_implemented") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
        and manifest.get("raw_payload_retention_allowed") is False
    )
    _add_check(checks, "manifest_no_execution_flags", safe, f"safe={safe}")


def _validate_coverage(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"requirement", "status", "minimum_contract", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "coverage_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["requirement"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    _add_check(checks, "coverage_provider_not_selected", rows.get("provider_selection") == "not_selected", f"provider_selection={rows.get('provider_selection')}")
    _add_check(checks, "coverage_intraday_frequency_required", rows.get("bar_frequency") == "required", f"bar_frequency={rows.get('bar_frequency')}")
    _add_check(checks, "coverage_raw_payload_blocked", rows.get("raw_payload_retention") == "blocked_by_default", f"raw_payload_retention={rows.get('raw_payload_retention')}")
    _add_check(checks, "coverage_rate_limits_required", rows.get("rate_limit_policy") == "required", f"rate_limit_policy={rows.get('rate_limit_policy')}")


def _validate_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "required", "semantic_contract", "notes"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "schema_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    fields = set(frame["field"].astype(str))
    missing_fields = sorted(REQUIRED_BAR_FIELDS - fields)
    required_rows = frame[frame["field"].astype(str).isin(REQUIRED_BAR_FIELDS)]
    all_required = required_rows["required"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "schema_required_bar_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "schema_core_fields_required", bool(all_required), f"all_required={bool(all_required)}")


def _validate_calendar(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"policy_item", "status", "rule", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "calendar_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    items = set(frame["policy_item"].astype(str))
    missing_items = sorted(REQUIRED_CALENDAR_ITEMS - items)
    all_required = frame["status"].astype(str).str.lower().eq("required").all()
    _add_check(checks, "calendar_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "calendar_all_required", bool(all_required), f"all_required={bool(all_required)}")


def _validate_costs(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"cost_component", "status", "minimum_contract", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "costs_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    components = set(frame["cost_component"].astype(str))
    missing_components = sorted(REQUIRED_COST_COMPONENTS - components)
    all_required = frame["status"].astype(str).str.lower().eq("required").all()
    _add_check(checks, "costs_required_components", not missing_components, f"missing={missing_components}")
    _add_check(checks, "costs_all_required", bool(all_required), f"all_required={bool(all_required)}")


def _validate_blocked(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"action", "status", "reason"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "blocked_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_required_actions", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_all_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "contract_dir": str(path),
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "GAPREV_INTRADAY_DATA_CONTRACT_PASS" if failed == 0 else "GAPREV_INTRADAY_DATA_CONTRACT_FAIL",
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
