from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "delisted_data_source_gate_manifest.json",
    "blocked_actions.csv",
    "candidate_source_matrix.csv",
    "required_dataset_contract.csv",
    "pdufa_real_backtest_unlock_requirements.csv",
    "source_decision_rule.csv",
]

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "market_data_download",
    "run_backtest",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}

REQUIRED_SOURCE_COLUMNS = {
    "provider",
    "official_source_url",
    "delisted_symbols",
    "survivorship_free_prices",
    "listing_dates",
    "delisting_dates",
    "corporate_actions",
    "pit_membership",
    "biotech_filter_support",
    "gate_status",
    "notes",
}

REQUIRED_DATASET_REQUIREMENTS = {
    "historical_delisted_common_stocks",
    "daily_ohlcv_adjusted",
    "listing_date",
    "delisting_date",
    "corporate_action_adjustments",
    "pit_membership_or_reconstructable_membership",
    "security_type_common_stock",
    "exchange_metadata",
    "license_allows_derived_research_artifacts",
}

REQUIRED_UNLOCK_REQUIREMENTS = {
    "survivorship_free_universe",
    "delisted_price_panel",
    "biotech_universe_filter",
    "pdufa_calendar_point_in_time",
    "event_entry_exit_rule_freeze",
    "no_hold_through_binary_event",
    "benchmark_comparison",
    "portfolio_diagnostics",
}


def validate_delisted_data_source_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        _add_check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(path, checks)

    manifest = _read_json(path / "delisted_data_source_gate_manifest.json", checks)
    blocked_actions = _read_csv(path / "blocked_actions.csv", checks, "blocked_actions.csv")
    source_matrix = _read_csv(path / "candidate_source_matrix.csv", checks, "candidate_source_matrix.csv")
    dataset_contract = _read_csv(path / "required_dataset_contract.csv", checks, "required_dataset_contract.csv")
    unlock_requirements = _read_csv(path / "pdufa_real_backtest_unlock_requirements.csv", checks, "pdufa_real_backtest_unlock_requirements.csv")
    decision_rule = _read_csv(path / "source_decision_rule.csv", checks, "source_decision_rule.csv")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if blocked_actions is not None:
        _validate_blocked_actions(blocked_actions, checks)
    if source_matrix is not None:
        _validate_source_matrix(source_matrix, checks)
    if dataset_contract is not None:
        _validate_dataset_contract(dataset_contract, checks)
    if unlock_requirements is not None:
        _validate_unlock_requirements(unlock_requirements, checks)
    if decision_rule is not None:
        _validate_decision_rule(decision_rule, checks)
    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the delisted data source gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_delisted_data_source_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    expected_flags = {
        "provider_query_allowed": False,
        "market_data_download_allowed": False,
        "backtest_allowed": False,
        "parameter_sweep_allowed": False,
        "short_selling_allowed": False,
        "paper_trading_allowed": False,
        "promotion_allowed": False,
    }
    execution_ok = all(manifest.get(field) is expected for field, expected in expected_flags.items())
    _add_check(checks, "manifest_gate_id", manifest.get("gate_id") == "DELISTED-DATA-SOURCE-GATE-001", str(manifest.get("gate_id")))
    _add_check(checks, "manifest_status", manifest.get("status") == "APPROVED_SOURCE_GATE_NOT_EXECUTABLE", str(manifest.get("status")))
    _add_check(checks, "manifest_no_execution_flags", execution_ok, {field: manifest.get(field) for field in expected_flags})
    _add_check(checks, "manifest_target_strategy", manifest.get("target_strategy") == "PDUFA Investment Mode", str(manifest.get("target_strategy")))
    _add_check(checks, "manifest_proxy_status", manifest.get("current_candidate_status") == "PROXY_INVESTMENT_CANDIDATE_ONLY", str(manifest.get("current_candidate_status")))


def _validate_blocked_actions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    if "action" not in frame.columns:
        _add_check(checks, "blocked_actions_column", False, str(frame.columns.tolist()))
        return
    actions = set(frame["action"].astype(str))
    _add_check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(actions), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - actions)}")


def _validate_source_matrix(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing_columns = sorted(REQUIRED_SOURCE_COLUMNS - set(frame.columns))
    _add_check(checks, "candidate_matrix_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    admissible = frame[frame["gate_status"].astype(str).str.lower().eq("admissible")]
    hard_fields = [
        "delisted_symbols",
        "survivorship_free_prices",
        "listing_dates",
        "delisting_dates",
        "corporate_actions",
        "pit_membership",
        "biotech_filter_support",
    ]
    if admissible.empty:
        _add_check(checks, "candidate_matrix_has_admissible_source", False, "no admissible rows")
        return
    hard_pass = admissible[hard_fields].astype(str).apply(lambda column: column.str.lower().eq("pass")).all(axis=1)
    _add_check(checks, "candidate_matrix_has_admissible_source", bool(hard_pass.any()), admissible[["provider", *hard_fields]].to_dict("records"))


def _validate_dataset_contract(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"requirement_id", "status", "why_required"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "dataset_contract_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    requirements = set(frame["requirement_id"].astype(str))
    statuses_ok = frame["status"].astype(str).str.lower().isin({"required", "blocked_until_available"}).all()
    _add_check(checks, "dataset_contract_required_requirements", REQUIRED_DATASET_REQUIREMENTS.issubset(requirements), f"missing={sorted(REQUIRED_DATASET_REQUIREMENTS - requirements)}")
    _add_check(checks, "dataset_contract_statuses", bool(statuses_ok), frame[["requirement_id", "status"]].to_dict("records"))


def _validate_unlock_requirements(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"requirement_id", "required_before_real_backtest", "failure_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "unlock_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    requirements = set(frame["requirement_id"].astype(str))
    all_required = frame["required_before_real_backtest"].astype(str).str.lower().eq("yes").all()
    all_block = frame["failure_action"].astype(str).str.lower().eq("block_real_backtest").all()
    _add_check(checks, "unlock_required_requirements", REQUIRED_UNLOCK_REQUIREMENTS.issubset(requirements), f"missing={sorted(REQUIRED_UNLOCK_REQUIREMENTS - requirements)}")
    _add_check(checks, "unlock_all_required", bool(all_required and all_block), f"all_required={bool(all_required)}; all_block={bool(all_block)}")


def _validate_decision_rule(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"decision_item", "rule"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "decision_rule_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    decisions = set(frame["decision_item"].astype(str))
    needed = {"current_status", "real_backtest_unlock", "blocked_if_no_delisted_prices", "blocked_if_no_pdufa_calendar"}
    _add_check(checks, "decision_rule_required_items", needed.issubset(decisions), f"missing={sorted(needed - decisions)}")


def _read_json(path: Path, checks: list[dict[str, str]]) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, str(exc))
        return None
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, f"csv_readable:{name}", False, str(exc))
        return None
    _add_check(checks, f"csv_readable:{name}", not frame.empty, f"rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "spec_dir": str(path),
        "status": "pass" if not failed else "fail",
        "gate_decision": "DELISTED_DATA_SOURCE_GATE_READY_NOT_EXECUTABLE" if not failed else "DELISTED_DATA_SOURCE_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
    }


if __name__ == "__main__":
    raise SystemExit(main())
