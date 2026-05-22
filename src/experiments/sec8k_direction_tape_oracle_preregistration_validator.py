from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "hypothesis.md",
    "allowed_features.csv",
    "parameter_freeze.csv",
    "decision_rule.csv",
    "blocked_actions.csv",
    "data_requirements.csv",
]

REQUIRED_FEATURES = {
    "sec8k_item_202_event_day",
    "reaction_session_date",
    "reaction_session_classification",
    "rth_first_15m_return",
    "rth_first_15m_volume_ratio",
    "rth_first_15m_vwap_position",
    "oracle_direction_label",
    "entry_timestamp",
    "intraday_exit_timestamp",
    "spread_proxy",
    "cost_model_bps",
}

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "download_intraday_data",
    "execute_backtest",
    "run_parameter_sweep",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "short_selling",
    "use_xmom_pnl_for_thresholds",
    "use_overlap_as_filter",
}

REQUIRED_DATA_REQUIREMENTS = {
    "sec8k_item_202_event_panel",
    "rth_intraday_bars",
    "trading_calendar",
    "timezone_policy",
    "spread_or_quote_proxy",
    "cost_model",
    "raw_payload_retention",
}


def validate_sec8k_direction_tape_oracle_preregistration(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        _add_check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))

    readme = _read_text(path / "README.md", checks, "markdown_readable:README.md")
    hypothesis = _read_text(path / "hypothesis.md", checks, "markdown_readable:hypothesis.md")
    features = _read_csv(path / "allowed_features.csv", checks, "csv_readable:allowed_features.csv")
    parameters = _read_csv(path / "parameter_freeze.csv", checks, "csv_readable:parameter_freeze.csv")
    decision = _read_csv(path / "decision_rule.csv", checks, "csv_readable:decision_rule.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    data_requirements = _read_csv(path / "data_requirements.csv", checks, "csv_readable:data_requirements.csv")

    if readme is not None and hypothesis is not None:
        _validate_markdown(readme, hypothesis, checks)
    if features is not None:
        _validate_features(features, checks)
    if parameters is not None:
        _validate_parameters(parameters, checks)
    if decision is not None:
        _validate_decision(decision, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if data_requirements is not None:
        _validate_data_requirements(data_requirements, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SEC 8-K Tape Oracle preregistration.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_sec8k_direction_tape_oracle_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_markdown(readme: str, hypothesis: str, checks: list[dict[str, str]]) -> None:
    combined = f"{readme}\n{hypothesis}"
    lower = combined.lower()
    _add_check(checks, "status_spec_only_not_executed", "SPEC_ONLY_NOT_EXECUTED" in combined, "SPEC_ONLY_NOT_EXECUTED present")
    _add_check(checks, "trial_id_present", "TRIAL-SEC8K-DIRECTION-001" in combined, "trial id present")
    _add_check(checks, "preregistration_id_present", "PREREG-SEC8K-DIRECTION-001" in combined, "preregistration id present")
    _add_check(checks, "long_only_positive_oracle_scope", "long-only positive oracle" in lower, "long-only positive oracle present")
    _add_check(checks, "no_xmom_threshold_reuse", "no thresholds selected from xmom" in lower, "XMOM threshold reuse barred")
    forbidden = ["paper trading authorized", "live trading authorized", "promotion authorized", "execution authorized"]
    _add_check(checks, "markdown_no_authorization_language", not any(marker in lower for marker in forbidden), "no authorization language")


def _validate_features(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"feature_name", "status", "definition", "lookahead_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "features_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    names = set(frame["feature_name"].astype(str))
    missing_features = sorted(REQUIRED_FEATURES - names)
    future_forbidden = {"same_day_close_return", "post_entry_return", "trade_pnl", "future_gap_fill"}
    future_rows = frame[frame["feature_name"].astype(str).isin(future_forbidden)]
    future_blocked = not future_rows.empty and future_rows["status"].astype(str).str.lower().eq("blocked_as_feature").all()
    required_lookahead_ok = not frame[frame["feature_name"].astype(str).isin(REQUIRED_FEATURES)]["lookahead_policy"].astype(str).str.lower().str.contains("future").any()
    _add_check(checks, "features_required_set", not missing_features, f"missing={missing_features}")
    _add_check(checks, "features_future_labels_blocked", bool(future_blocked), f"future_blocked={bool(future_blocked)}")
    _add_check(checks, "features_no_future_required_inputs", bool(required_lookahead_ok), f"lookahead_ok={bool(required_lookahead_ok)}")


def _validate_parameters(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"parameter_name", "status", "value", "change_after_execution_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "parameters_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    params = {str(row["parameter_name"]): str(row["value"]) for _, row in frame.iterrows()}
    exact = {
        "trial_status": "SPEC_ONLY_NOT_EXECUTED",
        "candidate_trade_side": "long_only_positive_oracle",
        "oracle_window": "09:30-09:45 America/New_York",
        "entry_time": "09:46 America/New_York",
        "exit_policy": "same_day_flat_by_15:55",
        "volume_ratio_threshold": "3.0",
        "cost_model_bps": "500",
        "dsr_threshold": "0.95",
        "minimum_trade_count": "30",
    }
    for name, value in exact.items():
        _add_check(checks, f"parameter_{name}_locked", params.get(name) == value, f"{name}={params.get(name)}")
    no_tbd = not any("TBD" in value for value in params.values())
    _add_check(checks, "parameters_no_tbd", no_tbd, "no TBD values")
    all_frozen = frame["status"].astype(str).str.lower().isin({"frozen", "blocked"}).all()
    _add_check(checks, "parameters_all_frozen_or_blocked", bool(all_frozen), f"all_frozen={bool(all_frozen)}")


def _validate_decision(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"decision_item", "status", "rule"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "decision_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["decision_item"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    required_items = {
        "execution_precondition",
        "direction_source",
        "primary_metric",
        "cost_gate",
        "sample_size_gate",
        "dsr_gate",
        "outlier_gate",
        "promotion_rule",
        "stop_rule",
    }
    missing_items = sorted(required_items - set(rows))
    _add_check(checks, "decision_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "decision_execution_blocked", rows.get("execution_precondition") == "blocked", f"execution={rows.get('execution_precondition')}")
    _add_check(checks, "decision_direction_required", rows.get("direction_source") == "required", f"direction={rows.get('direction_source')}")
    _add_check(checks, "decision_cost_gate_required", rows.get("cost_gate") == "required", f"cost={rows.get('cost_gate')}")
    _add_check(checks, "decision_promotion_blocked", rows.get("promotion_rule") == "blocked", f"promotion={rows.get('promotion_rule')}")


def _validate_blocked_actions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"action", "status", "reason"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "blocked_actions_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_actions_required_set", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_actions_all_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _validate_data_requirements(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"requirement", "status", "minimum_contract", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "data_requirements_columns", not missing, f"missing={missing}")
    if missing:
        return
    requirements = set(frame["requirement"].astype(str))
    rows = {str(row["requirement"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    missing_requirements = sorted(REQUIRED_DATA_REQUIREMENTS - requirements)
    _add_check(checks, "data_requirements_required_set", not missing_requirements, f"missing={missing_requirements}")
    _add_check(checks, "data_sec8k_panel_required_existing", rows.get("sec8k_item_202_event_panel") == "required_existing_artifact", f"sec8k={rows.get('sec8k_item_202_event_panel')}")
    _add_check(checks, "data_intraday_required_future", rows.get("rth_intraday_bars") == "required_future_gate", f"intraday={rows.get('rth_intraday_bars')}")
    _add_check(checks, "data_raw_payload_blocked_by_default", rows.get("raw_payload_retention") == "blocked_by_default", f"raw_payload={rows.get('raw_payload_retention')}")


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "spec_dir": str(path),
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC8K_DIRECTION_TAPE_ORACLE_PREREGISTRATION_PASS" if failed == 0 else "SEC8K_DIRECTION_TAPE_ORACLE_PREREGISTRATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
