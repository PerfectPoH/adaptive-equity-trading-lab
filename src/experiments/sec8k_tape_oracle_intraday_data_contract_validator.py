from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "intraday_data_contract_manifest.json",
    "event_panel_requirements.csv",
    "intraday_coverage_requirements.csv",
    "bar_schema_requirements.csv",
    "oracle_window_policy.csv",
    "calendar_and_session_policy.csv",
    "execution_cost_proxy_requirements.csv",
    "blocked_actions.csv",
]

REQUIRED_EVENT_ITEMS = {
    "sec8k_item_202_event_panel",
    "reaction_session_date",
    "reaction_session_classification",
    "bmo_amc_only",
    "dmt_unspecified_purge",
}
REQUIRED_BAR_FIELDS = {"symbol", "timestamp", "open", "high", "low", "close", "volume", "dollar_volume"}
REQUIRED_ORACLE_ITEMS = {
    "oracle_start",
    "oracle_end",
    "entry_time",
    "flat_time",
    "volume_baseline",
    "volume_ratio_threshold",
    "positive_oracle_rule",
    "negative_oracle_policy",
}
REQUIRED_CALENDAR_ITEMS = {
    "session_timezone",
    "regular_open",
    "regular_close",
    "holidays",
    "early_closes",
    "halt_policy",
}
REQUIRED_COST_COMPONENTS = {
    "spread_proxy",
    "slippage_model",
    "market_impact_model",
    "commission_model",
    "cost_model_bps",
    "no_gross_only_metrics",
}
REQUIRED_BLOCKED_ACTIONS = {
    "select_provider",
    "provider_query",
    "download_intraday_data",
    "implement_extractor",
    "compute_oracle_signals",
    "execute_backtest",
    "run_parameter_sweep",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "short_selling",
}


def validate_sec8k_tape_oracle_intraday_data_contract(contract_dir: str | Path) -> dict[str, Any]:
    path = Path(contract_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "contract_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        _add_check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))

    manifest = _read_json(path / "intraday_data_contract_manifest.json", checks, "manifest_json")
    event_panel = _read_csv(path / "event_panel_requirements.csv", checks, "csv_readable:event_panel_requirements.csv")
    coverage = _read_csv(path / "intraday_coverage_requirements.csv", checks, "csv_readable:intraday_coverage_requirements.csv")
    schema = _read_csv(path / "bar_schema_requirements.csv", checks, "csv_readable:bar_schema_requirements.csv")
    oracle = _read_csv(path / "oracle_window_policy.csv", checks, "csv_readable:oracle_window_policy.csv")
    calendar = _read_csv(path / "calendar_and_session_policy.csv", checks, "csv_readable:calendar_and_session_policy.csv")
    costs = _read_csv(path / "execution_cost_proxy_requirements.csv", checks, "csv_readable:execution_cost_proxy_requirements.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    readme = _read_text(path / "README.md", checks, "markdown_readable:README.md")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if readme is not None:
        _validate_readme(readme, checks)
    if event_panel is not None:
        _validate_required_items(event_panel, "requirement", REQUIRED_EVENT_ITEMS, checks, "event_panel")
    if coverage is not None:
        _validate_coverage(coverage, checks)
    if schema is not None:
        _validate_schema(schema, checks)
    if oracle is not None:
        _validate_oracle(oracle, checks)
    if calendar is not None:
        _validate_required_items(calendar, "policy_item", REQUIRED_CALENDAR_ITEMS, checks, "calendar")
    if costs is not None:
        _validate_costs(costs, checks)
    if blocked is not None:
        _validate_blocked(blocked, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SEC8K Tape Oracle intraday data-contract gate.")
    parser.add_argument("--contract-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_sec8k_tape_oracle_intraday_data_contract(args.contract_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    _add_check(checks, "manifest_status_spec_only", manifest.get("status") == "SPEC_ONLY_NOT_QUERIED", f"status={manifest.get('status')}")
    identity_ok = manifest.get("gate_id") == "SEC8K-TAPE-ORACLE-INTRADAY-DATA-CONTRACT-001" and manifest.get("trial_id") == "TRIAL-SEC8K-DIRECTION-001"
    _add_check(checks, "manifest_identity", identity_ok, f"gate={manifest.get('gate_id')}; trial={manifest.get('trial_id')}")
    safe = (
        manifest.get("provider_selected") is False
        and manifest.get("provider_query_performed") is False
        and manifest.get("network_call_performed") is False
        and manifest.get("market_data_downloaded") is False
        and manifest.get("extractor_implemented") is False
        and manifest.get("oracle_signals_computed") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
        and manifest.get("raw_payload_retention_allowed") is False
    )
    _add_check(checks, "manifest_no_execution_flags", safe, f"safe={safe}")


def _validate_readme(readme: str, checks: list[dict[str, str]]) -> None:
    _add_check(checks, "readme_trial_present", "TRIAL-SEC8K-DIRECTION-001" in readme, "trial id")
    _add_check(checks, "readme_status_present", "SPEC_ONLY_NOT_QUERIED" in readme, "status")
    lower = readme.lower()
    forbidden = ["paper trading authorized", "live trading authorized", "execution authorized", "promotion authorized"]
    _add_check(checks, "readme_no_authorization_language", not any(marker in lower for marker in forbidden), "no authorization language")


def _validate_coverage(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"requirement", "status", "minimum_contract", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "coverage_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["requirement"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    _add_check(checks, "coverage_provider_not_selected", rows.get("provider_selection") == "not_selected", f"provider={rows.get('provider_selection')}")
    _add_check(checks, "coverage_intraday_frequency_required", rows.get("bar_frequency") == "required", f"bar_frequency={rows.get('bar_frequency')}")
    _add_check(checks, "coverage_rth_only_required", rows.get("rth_session_only") == "required", f"rth={rows.get('rth_session_only')}")
    _add_check(checks, "coverage_raw_payload_blocked", rows.get("raw_payload_retention") == "blocked_by_default", f"raw={rows.get('raw_payload_retention')}")


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


def _validate_oracle(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"policy_item", "status", "rule", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "oracle_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    items = set(frame["policy_item"].astype(str))
    missing_items = sorted(REQUIRED_ORACLE_ITEMS - items)
    rows = {str(row["policy_item"]): str(row["rule"]) for _, row in frame.iterrows()}
    _add_check(checks, "oracle_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "oracle_start_locked", rows.get("oracle_start") == "09:30 America/New_York", f"start={rows.get('oracle_start')}")
    _add_check(checks, "oracle_end_locked", rows.get("oracle_end") == "09:45 America/New_York", f"end={rows.get('oracle_end')}")
    _add_check(checks, "oracle_entry_locked", rows.get("entry_time") == "09:46 America/New_York", f"entry={rows.get('entry_time')}")
    _add_check(checks, "oracle_flat_locked", rows.get("flat_time") == "15:55 America/New_York", f"flat={rows.get('flat_time')}")
    _add_check(checks, "oracle_volume_threshold_locked", "3.0" in rows.get("volume_ratio_threshold", ""), f"vol={rows.get('volume_ratio_threshold')}")


def _validate_costs(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"cost_component", "status", "minimum_contract", "failure_action"}
    missing = sorted(required_columns - set(frame.columns))
    _add_check(checks, "costs_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    components = set(frame["cost_component"].astype(str))
    missing_components = sorted(REQUIRED_COST_COMPONENTS - components)
    all_required = frame["status"].astype(str).str.lower().eq("required").all()
    cost_row = frame[frame["cost_component"].astype(str).eq("cost_model_bps")]
    cost_locked = not cost_row.empty and cost_row["minimum_contract"].astype(str).str.contains("500").all()
    _add_check(checks, "costs_required_components", not missing_components, f"missing={missing_components}")
    _add_check(checks, "costs_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "costs_500bps_required", bool(cost_locked), f"cost_locked={bool(cost_locked)}")


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


def _validate_required_items(frame: pd.DataFrame, column: str, required_items: set[str], checks: list[dict[str, str]], prefix: str) -> None:
    missing_column = column not in frame.columns
    _add_check(checks, f"{prefix}_item_column_present", not missing_column, f"column={column}")
    if missing_column:
        return
    items = set(frame[column].astype(str))
    missing_items = sorted(required_items - items)
    _add_check(checks, f"{prefix}_required_items", not missing_items, f"missing={missing_items}")


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
        "gate_decision": "SEC8K_TAPE_ORACLE_INTRADAY_DATA_CONTRACT_PASS" if failed == 0 else "SEC8K_TAPE_ORACLE_INTRADAY_DATA_CONTRACT_FAIL",
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
