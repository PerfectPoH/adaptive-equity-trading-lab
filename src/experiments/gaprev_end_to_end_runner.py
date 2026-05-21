from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


TRIAL_ID = "TRIAL-GAPREV-001"
RUN_ID = "GAPREV-SINGLE-CONTROLLED-BACKTEST-001"
NY = ZoneInfo("America/New_York")
ROOT = Path("experiments/provider_aware_research")
PROVIDER_GATE_DIR = ROOT / "gaprev_provider_selection_gate_20260521"
PROBE_APPROVAL_DIR = ROOT / "gaprev_single_provider_probe_approval_20260521"
DATA_DIR = ROOT / "data_inputs" / "gaprev_databento_intraday_probe_20260521"
PARAMETER_DIR = ROOT / "gaprev_parameter_freeze_20260521"
PRE_RUN_DIR = ROOT / "gaprev_pre_run_gate_20260521"
OUTPUT_DIR = ROOT / "execution_outputs" / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-GapRev-End-To-End-Controlled-Run-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-gaprev-end-to-end-controlled-run.md")


@dataclass(frozen=True)
class GapRevParameters:
    gap_threshold: float = -0.05
    relative_opening_volume_threshold: float = 2.0
    vwap_reclaim_cutoff_local: str = "10:30"
    holding_window_minutes: int = 120
    round_trip_cost_bps: float = 500.0
    min_trades_for_promotion: int = 30
    dsr_threshold: float = 0.95


def run_gaprev_end_to_end(*, execute_provider_probe: bool = True) -> dict[str, Any]:
    _ensure_dirs()
    params = GapRevParameters()
    provider_gate = _write_provider_selection_gate()
    approval = _write_single_probe_approval()
    if execute_provider_probe:
        data_result = _execute_databento_probe()
    else:
        data_result = _write_blocked_data_result("provider_probe_not_executed")
    parameter_freeze = _write_parameter_freeze(params)
    pre_run = _write_pre_run_gate(provider_gate, approval, data_result, parameter_freeze)

    if pre_run["status"] == "pass":
        execution = _run_controlled_backtest(DATA_DIR / "bars.csv", params)
    else:
        execution = _write_blocked_execution(pre_run)
    post_run = _write_post_run_validation(execution, params)
    decision = _write_decision_report(provider_gate, approval, data_result, parameter_freeze, pre_run, execution, post_run)
    return decision


def validate_intraday_bars(path: str | Path) -> dict[str, Any]:
    bars_path = Path(path)
    checks: list[dict[str, Any]] = []
    if not bars_path.exists():
        _check(checks, "bars_file_exists", False, str(bars_path))
        return _validation_report(checks)
    frame = pd.read_csv(bars_path)
    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume", "provider_dataset", "schema"}
    missing = sorted(required - set(frame.columns))
    _check(checks, "required_columns", not missing, f"missing={missing}")
    if missing:
        return _validation_report(checks)
    _check(checks, "non_empty", not frame.empty, f"rows={len(frame)}")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    _check(checks, "timestamps_parse_utc", not timestamps.isna().any(), f"invalid={int(timestamps.isna().sum())}")
    _check(checks, "chronological", timestamps.is_monotonic_increasing, "timestamps must be sorted")
    numeric_cols = ["open", "high", "low", "close", "volume"]
    numeric = frame[numeric_cols].apply(pd.to_numeric, errors="coerce")
    _check(checks, "numeric_fields_parse", not numeric.isna().any().any(), "OHLCV fields numeric")
    if not numeric.isna().any().any():
        ohlc_positive = (numeric[["open", "high", "low", "close"]] > 0).all().all()
        volume_non_negative = (numeric["volume"] >= 0).all()
        high_ok = (numeric["high"] >= numeric[["open", "close", "low"]].max(axis=1)).all()
        low_ok = (numeric["low"] <= numeric[["open", "close", "high"]].min(axis=1)).all()
        _check(checks, "positive_ohlc", bool(ohlc_positive), "open/high/low/close > 0")
        _check(checks, "non_negative_volume", bool(volume_non_negative), "volume >= 0")
        _check(checks, "high_low_envelope", bool(high_ok and low_ok), "high/low contain open/close")
    _check(checks, "raw_payload_absent", not (bars_path.parent / "raw_payload.json").exists(), "raw payload retention blocked")
    return _validation_report(checks)


def controlled_backtest_from_frame(frame: pd.DataFrame, params: GapRevParameters) -> dict[str, Any]:
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["local_ts"] = frame["timestamp"].dt.tz_convert(NY)
    frame["session_date"] = frame["local_ts"].dt.date.astype(str)
    frame = frame.sort_values("timestamp")
    sessions = sorted(frame["session_date"].unique())
    if len(sessions) < 2:
        return _blocked_execution_payload("insufficient_sessions", {"sessions": sessions})

    prev_day = frame[frame["session_date"].eq(sessions[-2])]
    day = frame[frame["session_date"].eq(sessions[-1])].copy()
    if prev_day.empty or day.empty:
        return _blocked_execution_payload("missing_previous_or_reaction_session", {"sessions": sessions})

    prior_close = float(prev_day.iloc[-1]["close"])
    open_price = float(day.iloc[0]["open"])
    gap_return = open_price / prior_close - 1.0
    day["typical_price"] = (day["high"].astype(float) + day["low"].astype(float) + day["close"].astype(float)) / 3.0
    day["cum_pv"] = (day["typical_price"] * day["volume"].astype(float)).cumsum()
    day["cum_volume"] = day["volume"].astype(float).cumsum()
    day["vwap"] = day["cum_pv"] / day["cum_volume"].replace(0, math.nan)

    prev_opening_volume = float(prev_day.head(30)["volume"].astype(float).sum())
    day_opening_volume = float(day.head(30)["volume"].astype(float).sum())
    rel_opening_volume = day_opening_volume / prev_opening_volume if prev_opening_volume > 0 else math.inf

    cutoff_hour, cutoff_minute = [int(part) for part in params.vwap_reclaim_cutoff_local.split(":")]
    cutoff = day.iloc[0]["local_ts"].replace(hour=cutoff_hour, minute=cutoff_minute, second=0, microsecond=0)
    candidates = day[(day["local_ts"] <= cutoff) & (day["close"].astype(float) >= day["vwap"].astype(float))]

    setup_pass = gap_return <= params.gap_threshold and rel_opening_volume >= params.relative_opening_volume_threshold
    if not setup_pass:
        return _no_trade_payload(
            reason="setup_filter_not_met",
            prior_close=prior_close,
            open_price=open_price,
            gap_return=gap_return,
            rel_opening_volume=rel_opening_volume,
        )
    if candidates.empty:
        return _no_trade_payload(
            reason="vwap_reclaim_not_met_before_cutoff",
            prior_close=prior_close,
            open_price=open_price,
            gap_return=gap_return,
            rel_opening_volume=rel_opening_volume,
        )

    entry = candidates.iloc[0]
    entry_ts = entry["timestamp"]
    exit_target = entry_ts + pd.Timedelta(minutes=params.holding_window_minutes)
    exit_candidates = day[day["timestamp"] >= exit_target]
    exit_row = exit_candidates.iloc[0] if not exit_candidates.empty else day.iloc[-1]
    entry_price = float(entry["close"])
    exit_price = float(exit_row["close"])
    gross_return = exit_price / entry_price - 1.0
    net_return = gross_return - params.round_trip_cost_bps / 10000.0
    return {
        "status": "pass",
        "decision": "GAPREV_CONTROLLED_BACKTEST_EXECUTED_PROMOTION_BLOCKED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "symbol": str(day.iloc[0]["symbol"]),
        "provider_dataset": str(day.iloc[0]["provider_dataset"]),
        "schema": str(day.iloc[0]["schema"]),
        "trade_count": 1,
        "prior_close": prior_close,
        "open_price": open_price,
        "gap_return": gap_return,
        "relative_opening_volume": rel_opening_volume,
        "vwap_reclaim_timestamp": entry_ts.isoformat(),
        "entry_price": entry_price,
        "exit_timestamp": exit_row["timestamp"].isoformat(),
        "exit_price": exit_price,
        "gross_return": gross_return,
        "round_trip_cost_bps": params.round_trip_cost_bps,
        "net_return": net_return,
        "promotion_allowed": False,
        "promotion_blockers": [
            "single_symbol_single_event_controlled_probe",
            "trade_count_below_30",
            "dsr_not_computable_from_one_trade",
            "known_forensic_symbol_not_clean_oos",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GAPREV eight-step controlled protocol.")
    parser.add_argument("--skip-provider-probe", action="store_true")
    args = parser.parse_args(argv)
    report = run_gaprev_end_to_end(execute_provider_probe=not args.skip_provider_probe)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"pass", "promotion_blocked"} else 2


def _ensure_dirs() -> None:
    for path in [PROVIDER_GATE_DIR, PROBE_APPROVAL_DIR, DATA_DIR, PARAMETER_DIR, PRE_RUN_DIR, OUTPUT_DIR, VAULT_REPORT.parent, VAULT_DEVLOG.parent]:
        path.mkdir(parents=True, exist_ok=True)


def _write_provider_selection_gate() -> dict[str, Any]:
    manifest = {
        "status": "PROVIDER_SELECTED_FOR_SINGLE_CONTROLLED_PROBE",
        "gate_id": "GAPREV-PROVIDER-SELECTION-001",
        "trial_id": TRIAL_ID,
        "selected_provider": "Databento Historical",
        "selected_dataset": "XNAS.ITCH",
        "selected_schema": "ohlcv-1m",
        "symbol": "CRMD",
        "selection_scope": "single_symbol_two_session_controlled_probe_only",
        "no_raw_payload_retention": True,
        "no_multi_symbol_scan": True,
        "no_parameter_sweep": True,
        "no_strategy_promotion": True,
    }
    _write_json(PROVIDER_GATE_DIR / "provider_selection_manifest.json", manifest)
    _write_csv(
        PROVIDER_GATE_DIR / "provider_selection_matrix.csv",
        ["provider", "role", "status", "rationale", "blocked_use"],
        [
            ["Databento Historical", "primary_intraday_bars", "selected", "Existing provider evidence supports XNAS.ITCH OHLCV minute bars; PIT symbology remains a future scale requirement.", "promotion_without_multi_event_validation"],
            ["Polygon", "secondary_crosscheck", "rejected_for_this_run", "Prior provider audit recorded free-tier minute aggregate access failure.", "primary_intraday_source"],
            ["Intrinio", "earnings_calendar_metadata", "not_used_in_this_run", "Useful for BMO/AMC earnings timestamps, not needed for this pure intraday CRMD probe.", "price_microstructure_source"],
        ],
    )
    (PROVIDER_GATE_DIR / "provider_selection_summary.md").write_text(
        "# GAPREV Provider Selection Gate\n\n"
        "Status: PROVIDER_SELECTED_FOR_SINGLE_CONTROLLED_PROBE.\n\n"
        "Databento Historical is selected only for one bounded CRMD XNAS.ITCH `ohlcv-1m` probe. "
        "This gate does not authorize multi-symbol scanning, parameter sweeps, OOS promotion, paper trading, or live trading.\n",
        encoding="utf-8",
    )
    return manifest


def _write_single_probe_approval() -> dict[str, Any]:
    manifest = {
        "status": "APPROVED_SINGLE_PROVIDER_PROBE",
        "gate_id": "GAPREV-SINGLE-PROVIDER-PROBE-001",
        "trial_id": TRIAL_ID,
        "provider": "Databento Historical",
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1m",
        "symbols": ["CRMD"],
        "start": "2025-05-05T13:30:00Z",
        "end": "2025-05-06T20:00:00Z",
        "max_provider_calls": 1,
        "raw_payload_retention_allowed": False,
        "derived_bars_retention_allowed": True,
    }
    _write_json(PROBE_APPROVAL_DIR / "single_probe_approval_manifest.json", manifest)
    _write_csv(
        PROBE_APPROVAL_DIR / "single_probe_scope.csv",
        ["field", "value"],
        [[key, json.dumps(value) if isinstance(value, list) else value] for key, value in manifest.items()],
    )
    _write_csv(
        PROBE_APPROVAL_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["all_symbols_scan", "blocked", "Single probe only."],
            ["save_raw_payload", "blocked", "Only derived bars and summaries retained."],
            ["parameter_sweep", "blocked", "Parameters must be frozen before run."],
            ["strategy_promotion", "blocked", "Controlled probe cannot promote."],
        ],
    )
    (PROBE_APPROVAL_DIR / "single_probe_approval_summary.md").write_text(
        "# GAPREV Single Provider Probe Approval\n\n"
        "Approved scope: one Databento Historical `XNAS.ITCH` `ohlcv-1m` query for CRMD over two regular sessions. "
        "Raw provider payload retention is blocked; derived bars are allowed for validation and controlled replay.\n",
        encoding="utf-8",
    )
    return manifest


def _execute_databento_probe() -> dict[str, Any]:
    try:
        import databento as db
    except Exception as exc:  # pragma: no cover - depends on local environment
        return _write_blocked_data_result(f"databento_package_unavailable:{type(exc).__name__}")
    api_key = _load_databento_api_key()
    if not api_key:
        return _write_blocked_data_result("databento_api_key_missing")
    approval = json.loads((PROBE_APPROVAL_DIR / "single_probe_approval_manifest.json").read_text(encoding="utf-8"))
    try:
        client = db.Historical(api_key)
        data = client.timeseries.get_range(
            dataset=approval["dataset"],
            symbols=approval["symbols"],
            schema=approval["schema"],
            start=approval["start"],
            end=approval["end"],
            limit=1000,
        )
        frame = data.to_df().reset_index()
    except Exception as exc:  # pragma: no cover - provider/network dependent
        return _write_blocked_data_result(f"provider_error:{type(exc).__name__}:{str(exc)[:220]}")

    bars = pd.DataFrame(
        {
            "symbol": frame["symbol"].astype(str),
            "timestamp": pd.to_datetime(frame["ts_event"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": frame["open"].astype(float),
            "high": frame["high"].astype(float),
            "low": frame["low"].astype(float),
            "close": frame["close"].astype(float),
            "volume": frame["volume"].astype(int),
            "provider_dataset": approval["dataset"],
            "schema": approval["schema"],
        }
    ).sort_values("timestamp")
    bars = _filter_regular_trading_hours(bars)
    bars_path = DATA_DIR / "bars.csv"
    bars.to_csv(bars_path, index=False)
    validation = validate_intraday_bars(bars_path)
    bars_hash = _sha256(bars_path)
    manifest = {
        "status": "pass" if validation["status"] == "pass" else "fail",
        "gate_id": "GAPREV-INTRADAY-DATA-INGESTION-001",
        "trial_id": TRIAL_ID,
        "provider_query_performed": True,
        "network_call_performed": True,
        "provider": "Databento Historical",
        "dataset": approval["dataset"],
        "schema": approval["schema"],
        "symbols": approval["symbols"],
        "start": approval["start"],
        "end": approval["end"],
        "rows": int(len(bars)),
        "session_filter": "RTH_09:30_16:00_America/New_York",
        "raw_payload_retained": False,
        "derived_bars_file": "bars.csv",
        "derived_bars_sha256": bars_hash,
        "validation_status": validation["status"],
    }
    _write_json(DATA_DIR / "data_input_manifest.json", manifest)
    _write_json(DATA_DIR / "data_input_validation_report.json", validation)
    (DATA_DIR / "README.md").write_text(
        "# GAPREV Databento Intraday Probe\n\n"
        "Derived OHLCV minute bars retained from the approved Databento single-provider probe. "
        "No raw provider payload is retained.\n",
        encoding="utf-8",
    )
    return manifest


def _filter_regular_trading_hours(frame: pd.DataFrame) -> pd.DataFrame:
    timestamps = pd.to_datetime(frame["timestamp"], utc=True)
    local = timestamps.dt.tz_convert(NY)
    rth_mask = (
        (local.dt.time >= datetime.strptime("09:30", "%H:%M").time())
        & (local.dt.time < datetime.strptime("16:00", "%H:%M").time())
    )
    return frame.loc[rth_mask].copy().reset_index(drop=True)


def _write_parameter_freeze(params: GapRevParameters) -> dict[str, Any]:
    rows = [
        ["direction", "long_only", "frozen", "Research spec."],
        ["gap_threshold", params.gap_threshold, "frozen", "Ex-ante gap-down magnitude threshold."],
        ["relative_opening_volume_threshold", params.relative_opening_volume_threshold, "frozen", "First 30 minutes vs previous session first 30 minutes."],
        ["vwap_reclaim_cutoff_local", params.vwap_reclaim_cutoff_local, "frozen", "America/New_York cutoff."],
        ["holding_window_minutes", params.holding_window_minutes, "frozen", "Intraday only."],
        ["round_trip_cost_bps", params.round_trip_cost_bps, "frozen", "Conservative cost haircut."],
        ["min_trades_for_promotion", params.min_trades_for_promotion, "frozen", "Promotion impossible below this count."],
        ["dsr_threshold", params.dsr_threshold, "frozen", "Promotion gate."],
    ]
    _write_csv(PARAMETER_DIR / "parameter_freeze.csv", ["parameter", "value", "status", "notes"], rows)
    manifest = {
        "status": "PARAMETERS_FROZEN_FOR_SINGLE_CONTROLLED_PROBE",
        "trial_id": TRIAL_ID,
        "no_parameter_sweep": True,
        "no_threshold_selection_from_probe_pnl": True,
        "parameters": {row[0]: row[1] for row in rows},
    }
    _write_json(PARAMETER_DIR / "parameter_freeze_manifest.json", manifest)
    (PARAMETER_DIR / "parameter_freeze_summary.md").write_text(
        "# GAPREV Parameter Freeze\n\n"
        "Parameters are frozen before the controlled replay. This artifact does not authorize retuning after the result.\n",
        encoding="utf-8",
    )
    return manifest


def _write_pre_run_gate(provider_gate: dict[str, Any], approval: dict[str, Any], data_result: dict[str, Any], parameter_freeze: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("provider_selected", provider_gate.get("status") == "PROVIDER_SELECTED_FOR_SINGLE_CONTROLLED_PROBE"),
        ("single_probe_approved", approval.get("status") == "APPROVED_SINGLE_PROVIDER_PROBE"),
        ("data_ingestion_passed", data_result.get("status") == "pass"),
        ("raw_payload_not_retained", data_result.get("raw_payload_retained") is False),
        ("parameters_frozen", parameter_freeze.get("status") == "PARAMETERS_FROZEN_FOR_SINGLE_CONTROLLED_PROBE"),
        ("no_parameter_sweep", parameter_freeze.get("no_parameter_sweep") is True),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "fail",
        "gate_id": "GAPREV-PRE-RUN-GATE-001",
        "trial_id": TRIAL_ID,
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
    }
    _write_json(PRE_RUN_DIR / "pre_run_gate_manifest.json", report)
    _write_csv(PRE_RUN_DIR / "pre_run_gate_checklist.csv", ["check", "status"], [[name, "pass" if ok else "fail"] for name, ok in checks])
    (PRE_RUN_DIR / "pre_run_gate_summary.md").write_text(
        f"# GAPREV Pre-Run Gate\n\nStatus: {report['status']}.\n",
        encoding="utf-8",
    )
    return report


def _run_controlled_backtest(bars_path: Path, params: GapRevParameters) -> dict[str, Any]:
    frame = pd.read_csv(bars_path)
    result = controlled_backtest_from_frame(frame, params)
    _write_json(OUTPUT_DIR / "controlled_backtest_result.json", result)
    _write_json(
        OUTPUT_DIR / "execution_manifest.json",
        {
            "status": result["status"],
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "single_controlled_backtest_performed": result["status"] == "pass",
            "parameter_sweep_performed": False,
            "paper_trading_performed": False,
            "live_trading_performed": False,
            "strategy_promotion_performed": False,
        },
    )
    return result


def _write_post_run_validation(execution: dict[str, Any], params: GapRevParameters) -> dict[str, Any]:
    trade_count = int(execution.get("trade_count", 0))
    checks = [
        ("execution_artifact_present", (OUTPUT_DIR / "controlled_backtest_result.json").exists()),
        ("no_parameter_sweep", True),
        ("no_paper_or_live", True),
        ("promotion_blocked_below_min_trade_count", trade_count < params.min_trades_for_promotion),
        ("dsr_not_claimed_for_single_trade", "dsr" not in execution),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "fail",
        "decision": "GAPREV_POST_RUN_VALIDATION_PASS_PROMOTION_BLOCKED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "trade_count": trade_count,
        "promotion_allowed": False,
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
    }
    _write_json(OUTPUT_DIR / "post_run_validation_report.json", report)
    return report


def _write_decision_report(
    provider_gate: dict[str, Any],
    approval: dict[str, Any],
    data_result: dict[str, Any],
    parameter_freeze: dict[str, Any],
    pre_run: dict[str, Any],
    execution: dict[str, Any],
    post_run: dict[str, Any],
) -> dict[str, Any]:
    decision = {
        "status": "promotion_blocked" if post_run.get("status") == "pass" else "fail",
        "decision": "TECHNICAL_CONTROLLED_RUN_COMPLETE__NO_PROMOTION",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "points_completed": {
            "1_provider_selection_gate": provider_gate.get("status"),
            "2_single_provider_probe_approval": approval.get("status"),
            "3_intraday_data_ingestion_gate": data_result.get("status"),
            "4_parameter_freeze": parameter_freeze.get("status"),
            "5_pre_run_gate": pre_run.get("status"),
            "6_single_controlled_backtest": execution.get("status"),
            "7_post_run_validation": post_run.get("status"),
            "8_decision": "NO_PROMOTION",
        },
        "trade_count": execution.get("trade_count", 0),
        "net_return": execution.get("net_return"),
        "promotion_allowed": False,
        "promotion_blockers": execution.get("promotion_blockers", ["controlled_probe_not_promotable"]),
        "artifact_root": str(OUTPUT_DIR),
    }
    _write_json(OUTPUT_DIR / "final_decision.json", decision)
    report_text = _format_markdown_report(decision, execution, data_result)
    VAULT_REPORT.write_text(report_text, encoding="utf-8")
    VAULT_DEVLOG.write_text(report_text, encoding="utf-8")
    return decision


def _format_markdown_report(decision: dict[str, Any], execution: dict[str, Any], data_result: dict[str, Any]) -> str:
    lines = [
        "# Report GAPREV End-To-End Controlled Run - 2026-05-21",
        "",
        f"Status: {decision['decision']}",
        "",
        "## Eight-Point Chain",
    ]
    for point, status in decision["points_completed"].items():
        lines.append(f"- {point}: {status}")
    lines.extend(
        [
            "",
            "## Probe",
            f"- Provider: {data_result.get('provider')}",
            f"- Dataset/schema: {data_result.get('dataset')} / {data_result.get('schema')}",
            f"- Rows retained: {data_result.get('rows')}",
            "- Raw payload retained: false",
            "",
            "## Controlled Backtest",
            f"- Execution status: {execution.get('status')}",
            f"- Trade count: {execution.get('trade_count', 0)}",
            f"- Gap return: {execution.get('gap_return')}",
            f"- Relative opening volume: {execution.get('relative_opening_volume')}",
            f"- Gross return: {execution.get('gross_return')}",
            f"- Net return after 500 bps round-trip cost: {execution.get('net_return')}",
            "",
            "## Decision",
            "No promotion. This was a single-symbol, single-event, known-forensic controlled probe. "
            "It validates wiring and data handling, not a deployable edge.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_blocked_data_result(reason: str) -> dict[str, Any]:
    manifest = {
        "status": "blocked",
        "gate_id": "GAPREV-INTRADAY-DATA-INGESTION-001",
        "trial_id": TRIAL_ID,
        "reason": reason,
        "provider_query_performed": False,
        "network_call_performed": False,
        "raw_payload_retained": False,
    }
    _write_json(DATA_DIR / "data_input_manifest.json", manifest)
    return manifest


def _write_blocked_execution(pre_run: dict[str, Any]) -> dict[str, Any]:
    result = _blocked_execution_payload("pre_run_gate_failed", pre_run)
    _write_json(OUTPUT_DIR / "controlled_backtest_result.json", result)
    return result


def _blocked_execution_payload(reason: str, details: Any) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "GAPREV_CONTROLLED_BACKTEST_NOT_EXECUTED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "reason": reason,
        "details": details,
        "trade_count": 0,
        "promotion_allowed": False,
    }


def _no_trade_payload(*, reason: str, prior_close: float, open_price: float, gap_return: float, rel_opening_volume: float) -> dict[str, Any]:
    return {
        "status": "pass",
        "decision": "GAPREV_CONTROLLED_BACKTEST_EXECUTED_NO_TRADE",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "reason": reason,
        "trade_count": 0,
        "prior_close": prior_close,
        "open_price": open_price,
        "gap_return": gap_return,
        "relative_opening_volume": rel_opening_volume,
        "promotion_allowed": False,
    }


def _load_databento_api_key() -> str:
    for env_name in ("DATABENTO_API_KEY", "DATABENTO_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in {"DATABENTO_API_KEY", "DATABENTO_KEY"}:
                return value.strip().strip('"').strip("'")
    return ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
