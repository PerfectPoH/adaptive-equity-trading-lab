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
    "overnight_gap_return",
    "relative_opening_volume",
    "vwap_reclaim_flag",
    "vwap_reclaim_time_minutes",
    "macro_trend_regime",
    "amihud_illiquidity",
    "spread_proxy",
    "known_catastrophic_event_flag",
}

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "download_intraday_data",
    "implement_extractor",
    "execute_backtest",
    "run_parameter_sweep",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "reuse_xmom_thresholds",
}

REQUIRED_DATA_REQUIREMENTS = {
    "intraday_bars",
    "corporate_actions",
    "trading_calendar",
    "spread_or_quote_proxy",
    "raw_payload_retention",
    "provider_rate_limits",
}


def validate_gap_down_reversion_preregistration(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

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
    args = _build_parser().parse_args(argv)
    report = validate_gap_down_reversion_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate spec-only gap-down reversion preregistration.")
    parser.add_argument("--spec-dir", required=True)
    return parser


def _validate_markdown(readme: str, hypothesis: str, checks: list[dict[str, str]]) -> None:
    combined = f"{readme}\n{hypothesis}"
    lower = combined.lower()
    _add_check(checks, "status_spec_only_not_executed", "SPEC_ONLY_NOT_EXECUTED" in combined, "SPEC_ONLY_NOT_EXECUTED present")
    _add_check(checks, "trial_id_present", "TRIAL-GAPREV-001" in combined, "trial id present")
    _add_check(checks, "preregistration_id_present", "PREREG-GAPREV-001" in combined, "preregistration id present")
    _add_check(checks, "long_only_scope_present", "long-only" in lower, "long-only scope present")
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
    future_label_blocked = frame[
        frame["feature_name"].astype(str).eq("intraday_holding_return")
    ]["status"].astype(str).str.lower().eq("blocked_as_feature").all()
    lookahead_ok = not frame[
        frame["feature_name"].astype(str).isin(REQUIRED_FEATURES)
    ]["lookahead_policy"].astype(str).str.lower().str.contains("future").any()
    _add_check(checks, "features_required_set", not missing_features, f"missing={missing_features}")
    _add_check(checks, "features_no_future_required_inputs", bool(lookahead_ok), f"lookahead_ok={bool(lookahead_ok)}")
    _add_check(checks, "features_future_return_blocked", bool(future_label_blocked), f"future_label_blocked={bool(future_label_blocked)}")


def _validate_parameters(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"parameter_name", "status", "value", "change_after_execution_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "parameters_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    params = {str(row["parameter_name"]): str(row["value"]) for _, row in frame.iterrows()}
    status_ok = params.get("trial_status") == "SPEC_ONLY_NOT_EXECUTED"
    direction_ok = params.get("direction") == "long_only"
    paper_live_blocked = params.get("paper_live_status") == "blocked"
    dsr_ok = params.get("dsr_threshold") == "0.95"
    tbd_params = {"gap_threshold", "relative_volume_threshold", "vwap_reclaim_cutoff", "holding_window_minutes", "stop_policy"}
    tbd_ok = all("TBD_IN_FUTURE_SPEC" in params.get(name, "") for name in tbd_params)
    _add_check(checks, "parameters_trial_status_spec_only", status_ok, f"trial_status={params.get('trial_status')}")
    _add_check(checks, "parameters_direction_long_only", direction_ok, f"direction={params.get('direction')}")
    _add_check(checks, "parameters_paper_live_blocked", paper_live_blocked, f"paper_live_status={params.get('paper_live_status')}")
    _add_check(checks, "parameters_dsr_threshold_locked", dsr_ok, f"dsr_threshold={params.get('dsr_threshold')}")
    _add_check(checks, "parameters_operational_thresholds_not_final", tbd_ok, "operational thresholds remain TBD")


def _validate_decision(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"decision_item", "status", "rule"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "decision_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["decision_item"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    required_items = {"execution_precondition", "data_precondition", "primary_metric", "robustness_gate", "sample_size_gate", "outlier_gate", "cost_gate", "promotion_rule", "stop_rule"}
    missing_items = sorted(required_items - set(rows))
    _add_check(checks, "decision_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "decision_execution_blocked", rows.get("execution_precondition") == "blocked", f"execution={rows.get('execution_precondition')}")
    _add_check(checks, "decision_promotion_blocked", rows.get("promotion_rule") == "blocked", f"promotion={rows.get('promotion_rule')}")
    _add_check(checks, "decision_cost_gate_required", rows.get("cost_gate") == "required", f"cost_gate={rows.get('cost_gate')}")
    _add_check(checks, "decision_outlier_gate_required", rows.get("outlier_gate") == "required", f"outlier_gate={rows.get('outlier_gate')}")


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
    missing_requirements = sorted(REQUIRED_DATA_REQUIREMENTS - requirements)
    rows = {str(row["requirement"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    _add_check(checks, "data_requirements_required_set", not missing_requirements, f"missing={missing_requirements}")
    _add_check(checks, "data_intraday_required", rows.get("intraday_bars") == "required", f"intraday_bars={rows.get('intraday_bars')}")
    _add_check(checks, "data_raw_payload_blocked_by_default", rows.get("raw_payload_retention") == "blocked_by_default", f"raw_payload_retention={rows.get('raw_payload_retention')}")


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
        "gate_decision": "GAPREV_PREREGISTRATION_SPEC_PASS" if failed == 0 else "GAPREV_PREREGISTRATION_SPEC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
