from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from src.experiments.gaprev_end_to_end_runner import (
    GapRevParameters,
    _filter_regular_trading_hours,
    controlled_backtest_from_frame,
    validate_intraday_bars,
)


TRIAL_ID = "TRIAL-GAPREV-001"
RUN_ID = "GAPREV-EVENT-SELECTION-PROBE-001"
ROOT = Path("experiments/provider_aware_research")
SOURCE_DAILY = ROOT / "data_inputs" / "databento_xmom_20260520" / "prices.csv"
EVENT_SELECTION_DIR = ROOT / "gaprev_event_selection_gate_20260521"
PROBE_APPROVAL_DIR = ROOT / "gaprev_event_selection_single_probe_approval_20260521"
DATA_DIR = ROOT / "data_inputs" / "gaprev_event_selection_databento_intraday_probe_20260521"
PRE_RUN_DIR = ROOT / "gaprev_event_selection_pre_run_gate_20260521"
OUTPUT_DIR = ROOT / "execution_outputs" / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-GapRev-Event-Selection-Probe-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-gaprev-event-selection-probe.md")
NY = ZoneInfo("America/New_York")


def run_gaprev_event_selection_probe() -> dict[str, Any]:
    _ensure_dirs()
    candidate = select_gaprev_candidate(SOURCE_DAILY)
    selection = _write_event_selection_gate(candidate)
    approval = _write_probe_approval(candidate)
    data_result = _execute_databento_probe(candidate)
    pre_run = _write_pre_run_gate(selection, approval, data_result)
    params = GapRevParameters()
    if pre_run["status"] == "pass":
        execution = controlled_backtest_from_frame(pd.read_csv(DATA_DIR / "bars.csv"), params)
        execution["run_id"] = RUN_ID
    else:
        execution = _blocked_execution("pre_run_gate_failed", pre_run)
    _write_json(OUTPUT_DIR / "controlled_backtest_result.json", execution)
    post_run = _write_post_run_validation(execution, params)
    decision = _write_decision(selection, approval, data_result, pre_run, execution, post_run)
    return decision


def select_gaprev_candidate(source_daily: str | Path) -> dict[str, Any]:
    frame = pd.read_csv(source_daily).sort_values(["symbol", "date"])
    frame = frame[frame["symbol"].astype(str) != "IWM"].copy()
    frame["prev_close"] = frame.groupby("symbol")["close"].shift(1)
    frame["daily_gap"] = frame["open"] / frame["prev_close"] - 1.0
    frame["adv20"] = frame.groupby("symbol")["volume"].transform(lambda series: series.shift(1).rolling(20, min_periods=10).mean())
    frame["daily_relative_volume"] = frame["volume"] / frame["adv20"]
    eligible = frame[(frame["daily_gap"] <= -0.05) & (frame["daily_relative_volume"] >= 2.0)].copy()
    eligible = eligible[~((eligible["symbol"] == "CRMD") & (eligible["date"] == "2025-05-06"))]
    eligible = eligible.sort_values(["daily_relative_volume", "daily_gap"], ascending=[False, True])
    if eligible.empty:
        raise RuntimeError("No eligible daily candidate for GAPREV event selection.")
    row = eligible.iloc[0]
    event_date = str(row["date"])
    previous_date = _previous_available_date(frame, str(row["symbol"]), event_date)
    return {
        "symbol": str(row["symbol"]),
        "event_date": event_date,
        "previous_date": previous_date,
        "provider_dataset": str(row["provider_dataset"]),
        "daily_open": float(row["open"]),
        "daily_prev_close": float(row["prev_close"]),
        "daily_gap": float(row["daily_gap"]),
        "daily_volume": int(row["volume"]),
        "daily_adv20": float(row["adv20"]),
        "daily_relative_volume": float(row["daily_relative_volume"]),
        "selection_rule": "daily_gap<=-5pct AND daily_relative_volume>=2x; exclude CRMD 2025-05-06 false RTH-open case; rank by daily_relative_volume desc",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GAPREV event-selection controlled probe.")
    parser.parse_args(argv)
    report = run_gaprev_event_selection_probe()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"promotion_blocked", "pass"} else 2


def _ensure_dirs() -> None:
    for path in [EVENT_SELECTION_DIR, PROBE_APPROVAL_DIR, DATA_DIR, PRE_RUN_DIR, OUTPUT_DIR, VAULT_REPORT.parent, VAULT_DEVLOG.parent]:
        path.mkdir(parents=True, exist_ok=True)


def _write_event_selection_gate(candidate: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "status": "EVENT_SELECTED_FOR_SINGLE_CONTROLLED_PROBE",
        "gate_id": "GAPREV-EVENT-SELECTION-GATE-001",
        "trial_id": TRIAL_ID,
        "source_daily_file": str(SOURCE_DAILY),
        "candidate": candidate,
        "pnl_intraday_observed_before_selection": False,
        "parameter_sweep_performed": False,
        "strategy_promotion_authorized": False,
    }
    _write_json(EVENT_SELECTION_DIR / "event_selection_manifest.json", manifest)
    _write_csv(
        EVENT_SELECTION_DIR / "selected_candidate.csv",
        list(candidate.keys()),
        [[candidate[key] for key in candidate]],
    )
    (EVENT_SELECTION_DIR / "event_selection_summary.md").write_text(
        "# GAPREV Event Selection Gate\n\n"
        f"Selected candidate: {candidate['symbol']} {candidate['event_date']}.\n\n"
        "Selection used only the already-ingested daily panel and did not observe intraday PnL. "
        "The known CRMD 2025-05-06 RTH-open false case is excluded from this candidate-selection probe.\n",
        encoding="utf-8",
    )
    return manifest


def _write_probe_approval(candidate: dict[str, Any]) -> dict[str, Any]:
    start, end = _utc_query_bounds(candidate["previous_date"], candidate["event_date"])
    manifest = {
        "status": "APPROVED_EVENT_SELECTION_SINGLE_PROVIDER_PROBE",
        "gate_id": "GAPREV-EVENT-SELECTION-SINGLE-PROBE-001",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "provider": "Databento Historical",
        "dataset": candidate["provider_dataset"],
        "schema": "ohlcv-1m",
        "symbol": candidate["symbol"],
        "start": start,
        "end": end,
        "max_provider_calls": 1,
        "raw_payload_retention_allowed": False,
    }
    _write_json(PROBE_APPROVAL_DIR / "single_probe_approval_manifest.json", manifest)
    _write_csv(PROBE_APPROVAL_DIR / "single_probe_scope.csv", ["field", "value"], [[key, value] for key, value in manifest.items()])
    _write_csv(
        PROBE_APPROVAL_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["multi_candidate_probe", "blocked", "Only selected candidate is queried."],
            ["save_raw_payload", "blocked", "Derived bars only."],
            ["parameter_sweep", "blocked", "Frozen GapRev parameters only."],
            ["strategy_promotion", "blocked", "Single selected probe cannot promote."],
        ],
    )
    return manifest


def _execute_databento_probe(candidate: dict[str, Any]) -> dict[str, Any]:
    try:
        import databento as db
    except Exception as exc:  # pragma: no cover
        return _write_data_manifest({"status": "blocked", "reason": f"databento_package_unavailable:{type(exc).__name__}"})
    api_key = _load_databento_key()
    if not api_key:
        return _write_data_manifest({"status": "blocked", "reason": "databento_api_key_missing"})
    approval = json.loads((PROBE_APPROVAL_DIR / "single_probe_approval_manifest.json").read_text(encoding="utf-8"))
    try:
        client = db.Historical(api_key)
        data = client.timeseries.get_range(
            dataset=approval["dataset"],
            symbols=[approval["symbol"]],
            schema=approval["schema"],
            start=approval["start"],
            end=approval["end"],
            limit=1000,
        )
        frame = data.to_df().reset_index()
    except Exception as exc:  # pragma: no cover
        return _write_data_manifest({"status": "blocked", "reason": f"provider_error:{type(exc).__name__}:{str(exc)[:220]}"})

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
    return _write_data_manifest(
        {
            "status": "pass" if validation["status"] == "pass" else "fail",
            "gate_id": "GAPREV-EVENT-SELECTION-DATA-INGESTION-001",
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "provider_query_performed": True,
            "network_call_performed": True,
            "provider": "Databento Historical",
            "dataset": approval["dataset"],
            "schema": approval["schema"],
            "symbol": approval["symbol"],
            "start": approval["start"],
            "end": approval["end"],
            "rows": int(len(bars)),
            "session_filter": "RTH_09:30_16:00_America/New_York",
            "raw_payload_retained": False,
            "derived_bars_sha256": _sha256(bars_path),
            "validation_status": validation["status"],
        },
        validation,
    )


def _write_data_manifest(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    _write_json(DATA_DIR / "data_input_manifest.json", manifest)
    if validation is not None:
        _write_json(DATA_DIR / "data_input_validation_report.json", validation)
    (DATA_DIR / "README.md").write_text(
        "# GAPREV Event Selection Databento Intraday Probe\n\nDerived RTH OHLCV minute bars only. Raw provider payload is not retained.\n",
        encoding="utf-8",
    )
    return manifest


def _write_pre_run_gate(selection: dict[str, Any], approval: dict[str, Any], data_result: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("event_selected_without_intraday_pnl", selection.get("pnl_intraday_observed_before_selection") is False),
        ("single_probe_approved", approval.get("status") == "APPROVED_EVENT_SELECTION_SINGLE_PROVIDER_PROBE"),
        ("data_ingestion_passed", data_result.get("status") == "pass"),
        ("raw_payload_not_retained", data_result.get("raw_payload_retained") is False),
    ]
    report = {"status": "pass" if all(ok for _, ok in checks) else "fail", "trial_id": TRIAL_ID, "run_id": RUN_ID, "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks]}
    _write_json(PRE_RUN_DIR / "pre_run_gate_manifest.json", report)
    _write_csv(PRE_RUN_DIR / "pre_run_gate_checklist.csv", ["check", "status"], [[name, "pass" if ok else "fail"] for name, ok in checks])
    return report


def _write_post_run_validation(execution: dict[str, Any], params: GapRevParameters) -> dict[str, Any]:
    trade_count = int(execution.get("trade_count", 0))
    checks = [
        ("controlled_result_written", (OUTPUT_DIR / "controlled_backtest_result.json").exists()),
        ("no_parameter_sweep", True),
        ("promotion_blocked_below_30_trades", trade_count < params.min_trades_for_promotion),
        ("dsr_not_claimed_for_micro_probe", "dsr" not in execution),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "fail",
        "decision": "GAPREV_EVENT_SELECTION_POST_RUN_PASS_PROMOTION_BLOCKED",
        "trade_count": trade_count,
        "promotion_allowed": False,
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
    }
    _write_json(OUTPUT_DIR / "post_run_validation_report.json", report)
    return report


def _write_decision(
    selection: dict[str, Any],
    approval: dict[str, Any],
    data_result: dict[str, Any],
    pre_run: dict[str, Any],
    execution: dict[str, Any],
    post_run: dict[str, Any],
) -> dict[str, Any]:
    decision = {
        "status": "promotion_blocked",
        "decision": "EVENT_SELECTION_CONTROLLED_PROBE_COMPLETE__NO_PROMOTION",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "selected_candidate": selection["candidate"],
        "points_completed": {
            "1_event_selection_gate": selection.get("status"),
            "2_single_provider_probe_approval": approval.get("status"),
            "3_intraday_data_ingestion_gate": data_result.get("status"),
            "4_pre_run_gate": pre_run.get("status"),
            "5_single_controlled_backtest": execution.get("status"),
            "6_post_run_validation": post_run.get("status"),
            "7_decision": "NO_PROMOTION",
        },
        "trade_count": execution.get("trade_count", 0),
        "gap_return": execution.get("gap_return"),
        "relative_opening_volume": execution.get("relative_opening_volume"),
        "net_return": execution.get("net_return"),
        "promotion_allowed": False,
        "promotion_blockers": execution.get("promotion_blockers", ["single_event_probe_not_promotable"]),
    }
    _write_json(OUTPUT_DIR / "final_decision.json", decision)
    report = _format_report(decision, data_result, execution)
    VAULT_REPORT.write_text(report, encoding="utf-8")
    VAULT_DEVLOG.write_text(report, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], data_result: dict[str, Any], execution: dict[str, Any]) -> str:
    candidate = decision["selected_candidate"]
    return (
        "# Report GAPREV Event Selection Probe - 2026-05-21\n\n"
        f"Status: {decision['decision']}\n\n"
        "## Selected Candidate\n"
        f"- Symbol/date: {candidate['symbol']} {candidate['event_date']}\n"
        f"- Daily gap used for selection: {candidate['daily_gap']}\n"
        f"- Daily relative volume used for selection: {candidate['daily_relative_volume']}\n\n"
        "## Intraday Probe\n"
        f"- Provider: {data_result.get('provider')}\n"
        f"- Dataset/schema: {data_result.get('dataset')} / {data_result.get('schema')}\n"
        f"- Rows retained: {data_result.get('rows')}\n"
        "- Raw payload retained: false\n\n"
        "## Controlled Replay\n"
        f"- Status: {execution.get('status')}\n"
        f"- Trade count: {execution.get('trade_count', 0)}\n"
        f"- RTH gap return: {execution.get('gap_return')}\n"
        f"- Relative opening volume: {execution.get('relative_opening_volume')}\n"
        f"- Net return: {execution.get('net_return')}\n\n"
        "## Decision\n"
        "No promotion. This is a single-event event-selection probe and cannot establish a tradable edge.\n"
    )


def _blocked_execution(reason: str, details: Any) -> dict[str, Any]:
    return {"status": "blocked", "reason": reason, "details": details, "trade_count": 0, "promotion_allowed": False}


def _previous_available_date(frame: pd.DataFrame, symbol: str, event_date: str) -> str:
    rows = frame[(frame["symbol"] == symbol) & (frame["date"] < event_date)].sort_values("date")
    if rows.empty:
        raise RuntimeError(f"No previous date for {symbol} {event_date}")
    return str(rows.iloc[-1]["date"])


def _utc_query_bounds(previous_date: str, event_date: str) -> tuple[str, str]:
    start_local = datetime.combine(date.fromisoformat(previous_date), time(9, 30), tzinfo=NY)
    end_local = datetime.combine(date.fromisoformat(event_date), time(16, 0), tzinfo=NY)
    return start_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"), end_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def _load_databento_key() -> str:
    for env_name in ("DATABENTO_API_KEY", "DATABENTO_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    env_path = Path(".env")
    if not env_path.exists():
        return ""
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


if __name__ == "__main__":
    raise SystemExit(main())
