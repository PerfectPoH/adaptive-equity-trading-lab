from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import dotenv_values

from src.experiments.sec8k_tape_oracle_existing_intraday_backtest import (
    EVENT_PANEL,
    run_existing_intraday_backtest,
    validate_existing_intraday_backtest,
)


RUN_ID = "SEC8K-TAPE-ORACLE-DATABENTO-MINI-PANEL-001"
DATASET = "XNAS.ITCH"
SCHEMA = "ohlcv-1m"
MAX_EVENTS = 30
CONTROL_SESSIONS = 5
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
DATA_DIR = Path("experiments/provider_aware_research/data_inputs/sec8k_tape_oracle_databento_mini_panel_20260522")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/SEC8K-TAPE-ORACLE-DATABENTO-MINI-PANEL-BACKTEST-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC8K-Tape-Oracle-Databento-Mini-Panel-Backtest-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-sec8k-tape-oracle-databento-mini-panel-backtest.md")


def run_databento_mini_panel_and_backtest(
    *,
    event_panel_path: str | Path = EVENT_PANEL,
    price_file: str | Path = PRICE_FILE,
    data_dir: str | Path = DATA_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    max_events: int = MAX_EVENTS,
    control_sessions: int = CONTROL_SESSIONS,
) -> dict[str, Any]:
    data_root = Path(data_dir)
    data_root.mkdir(parents=True, exist_ok=True)
    key = _resolve_databento_key()
    approval = build_approval(max_events=max_events, control_sessions=control_sessions, key_present=bool(key))
    _write_json(data_root / "approval_manifest.json", approval)
    if not key:
        decision = _blocked_decision("DATABENTO_API_KEY_MISSING", data_root, output_dir)
        return decision
    cases = select_event_cases(event_panel_path, price_file, max_events=max_events, control_sessions=control_sessions)
    _write_csv(data_root / "selected_cases.csv", list(cases[0].keys()) if cases else [], cases)
    query_results = []
    for case in cases:
        query_results.append(fetch_case_bars(case, key, data_root))
    _write_csv(data_root / "query_results.csv", list(query_results[0].keys()) if query_results else [], query_results)
    _write_json(data_root / "dataset_manifest.json", summarize_queries(query_results, max_events=max_events))
    decision = run_existing_intraday_backtest(
        event_panel_path=event_panel_path,
        intraday_root=data_root,
        output_dir=output_dir,
    )
    validation = validate_existing_intraday_backtest(output_dir)
    _write_json(Path(output_dir) / "mini_panel_validation_report.json", validation)
    write_vault_report(data_root, Path(output_dir), decision)
    return decision


def build_approval(max_events: int, control_sessions: int, key_present: bool) -> dict[str, Any]:
    return {
        "approval_id": "APPROVAL-SEC8K-TAPE-ORACLE-DATABENTO-MINI-PANEL-001",
        "run_id": RUN_ID,
        "provider": "Databento",
        "dataset": DATASET,
        "schema": SCHEMA,
        "max_events": max_events,
        "max_provider_calls": max_events,
        "control_sessions_per_event": control_sessions,
        "raw_payload_retention": False,
        "api_key_present": key_present,
        "provider_query_scope": "bounded_one_call_per_selected_event",
        "parameter_sweep_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "promotion_allowed": False,
    }


def select_event_cases(
    event_panel_path: str | Path,
    price_file: str | Path,
    *,
    max_events: int,
    control_sessions: int,
) -> list[dict[str, Any]]:
    events = pd.read_csv(event_panel_path)
    prices = pd.read_csv(price_file)
    prices["date"] = pd.to_datetime(prices["date"]).dt.date.astype(str)
    calendars = {str(symbol): sorted(group["date"].astype(str).unique()) for symbol, group in prices.groupby("symbol")}
    rows = []
    eligible = events[events["status"].astype(str).eq("event")].copy()
    eligible = eligible.sort_values(["reaction_session_date", "symbol"])
    for _, event in eligible.iterrows():
        symbol = str(event["symbol"])
        event_date = str(event["reaction_session_date"])
        calendar = calendars.get(symbol, [])
        if event_date not in calendar:
            continue
        pos = calendar.index(event_date)
        if pos < control_sessions:
            continue
        controls = calendar[pos - control_sessions : pos]
        start_day = controls[0]
        end_day = event_date
        rows.append(
            {
                "symbol": symbol,
                "event_date": event_date,
                "control_dates": "|".join(controls),
                "start": _rth_open_utc(start_day),
                "end": _rth_close_utc(end_day),
                "dataset": DATASET,
                "schema": SCHEMA,
            }
        )
        if len(rows) >= max_events:
            break
    return rows


def fetch_case_bars(case: dict[str, Any], api_key: str, data_root: Path) -> dict[str, Any]:
    case_dir = data_root / f"{case['symbol']}_{case['event_date']}"
    case_dir.mkdir(parents=True, exist_ok=True)
    try:
        frame = _fetch_databento_frame(case, api_key)
    except Exception as exc:
        result = _query_result(case, "error", rows=0, detail=f"{type(exc).__name__}: {exc}", sha256="")
        _write_json(case_dir / "data_input_manifest.json", result)
        return result
    if frame.empty:
        result = _query_result(case, "empty", rows=0, detail="no_records", sha256="")
        _write_json(case_dir / "data_input_manifest.json", result)
        return result
    bars = normalize_bars(frame, str(case["symbol"]))
    bars_path = case_dir / "bars.csv"
    bars.to_csv(bars_path, index=False)
    digest = _sha256_file(bars_path)
    result = _query_result(case, "pass", rows=len(bars), detail="derived_bars_written_raw_not_retained", sha256=digest)
    result["bars_path"] = str(bars_path)
    _write_json(case_dir / "data_input_manifest.json", result)
    _write_json(case_dir / "data_input_validation_report.json", validate_case_bars(bars, str(case["event_date"])))
    return result


def normalize_bars(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    data = frame.reset_index().copy()
    rename = {col: str(col).lower() for col in data.columns}
    data = data.rename(columns=rename)
    ts_col = "ts_event" if "ts_event" in data.columns else "timestamp"
    if ts_col not in data.columns:
        ts_col = data.columns[0]
    out = pd.DataFrame(
        {
            "symbol": symbol,
            "timestamp": pd.to_datetime(data[ts_col], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": pd.to_numeric(data["open"], errors="coerce"),
            "high": pd.to_numeric(data["high"], errors="coerce"),
            "low": pd.to_numeric(data["low"], errors="coerce"),
            "close": pd.to_numeric(data["close"], errors="coerce"),
            "volume": pd.to_numeric(data["volume"], errors="coerce").fillna(0).astype(int),
            "provider_dataset": DATASET,
            "schema": SCHEMA,
        }
    )
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out.sort_values("timestamp").reset_index(drop=True)


def validate_case_bars(bars: pd.DataFrame, event_date: str) -> dict[str, Any]:
    checks = []
    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
    _check(checks, "required_columns", required.issubset(bars.columns), f"missing={sorted(required - set(bars.columns))}")
    _check(checks, "non_empty", len(bars) > 0, f"rows={len(bars)}")
    if not bars.empty:
        ts = pd.to_datetime(bars["timestamp"], utc=True)
        ny = ts.dt.tz_convert("America/New_York")
        event_rows = bars[ny.dt.date.astype(str).eq(event_date)]
        event_times = ny[ny.dt.date.astype(str).eq(event_date)].dt.time
        _check(checks, "event_day_present", not event_rows.empty, f"event_rows={len(event_rows)}")
        _check(checks, "oracle_window_present", any((event_times >= time(9, 30)) & (event_times < time(9, 45))), "09:30-09:45")
        _check(checks, "entry_time_present", any(event_times == time(9, 46)), "09:46")
        _check(checks, "flat_time_present", any(event_times == time(15, 55)), "15:55")
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {"status": "pass" if failed == 0 else "fail", "checks": checks, "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed}}


def summarize_queries(rows: list[dict[str, Any]], max_events: int) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "status": "complete",
        "max_events": max_events,
        "query_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "empty_count": sum(1 for row in rows if row["status"] == "empty"),
        "error_count": sum(1 for row in rows if row["status"] == "error"),
        "raw_payload_retained": False,
        "provider_query_performed": bool(rows),
        "market_data_downloaded": bool(rows),
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def write_vault_report(data_root: Path, output_dir: Path, decision: dict[str, Any]) -> None:
    manifest = json.loads((data_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((output_dir / "backtest_summary.json").read_text(encoding="utf-8"))
    mini_decision = "SEC8K_TAPE_ORACLE_MINI_PANEL_NO_PROMOTION_COST_AND_SAMPLE_BLOCKED"
    if summary["positive_oracle_trade_count"] == 0:
        mini_decision = "SEC8K_TAPE_ORACLE_MINI_PANEL_NO_TRADES"
    elif summary["net_return_sum_after_500bps"] >= 0 and summary["positive_oracle_trade_count"] >= 30:
        mini_decision = "SEC8K_TAPE_ORACLE_MINI_PANEL_CANDIDATE_REQUIRES_DSR_GATE"
    mini_panel_decision = {
        "status": "complete",
        "decision": mini_decision,
        "run_id": RUN_ID,
        "trial_id": "TRIAL-SEC8K-DIRECTION-001",
        "provider_query_performed": manifest["provider_query_performed"],
        "market_data_downloaded": manifest["market_data_downloaded"],
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "promotion_allowed": False,
        "query_count": manifest["query_count"],
        "evaluated_event_count": summary["evaluated_event_count"],
        "positive_oracle_trade_count": summary["positive_oracle_trade_count"],
        "net_return_sum_after_500bps": summary["net_return_sum_after_500bps"],
        "blockers": summary["blockers"],
    }
    _write_json(output_dir / "mini_panel_final_decision.json", mini_panel_decision)
    text = (
        "# Report SEC8K Tape Oracle Databento Mini Panel Backtest - 2026-05-22\n\n"
        f"Decision: `{mini_decision}`\n\n"
        "## Scope\n\n"
        "Bounded Databento mini-panel for SEC 8-K Tape Oracle. Raw payloads were not retained. No parameter sweep, paper/live trading, or promotion occurred.\n\n"
        "## Data\n\n"
        f"- Query count: {manifest['query_count']}\n"
        f"- Pass count: {manifest['pass_count']}\n"
        f"- Empty count: {manifest['empty_count']}\n"
        f"- Error count: {manifest['error_count']}\n\n"
        "## Backtest\n\n"
        f"- Evaluated event count: {summary['evaluated_event_count']}\n"
        f"- Positive oracle trade count: {summary['positive_oracle_trade_count']}\n"
        f"- Gross return sum: {summary['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {summary['net_return_sum_after_500bps']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Interpretation\n\n"
        "This is the first bounded live-data expansion of the SEC8K Tape Oracle branch. The result remains non-promotable unless sample size, costs, and statistical gates pass.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def _fetch_databento_frame(case: dict[str, Any], api_key: str) -> pd.DataFrame:
    import databento as db

    client = db.Historical(api_key)
    data = client.timeseries.get_range(
        dataset=str(case["dataset"]),
        schema=str(case["schema"]),
        symbols=str(case["symbol"]),
        start=str(case["start"]),
        end=str(case["end"]),
    )
    frame = data.to_df()
    return frame if frame is not None else pd.DataFrame()


def _resolve_databento_key() -> str:
    env_key = os.environ.get("DATABENTO_API_KEY", "")
    if env_key:
        return env_key
    env_path = Path(".env")
    if env_path.exists():
        return str(dotenv_values(env_path).get("DATABENTO_API_KEY") or "")
    return ""


def _rth_open_utc(date_text: str) -> str:
    return pd.Timestamp(f"{date_text} 09:30", tz="America/New_York").tz_convert("UTC").isoformat()


def _rth_close_utc(date_text: str) -> str:
    return pd.Timestamp(f"{date_text} 16:00", tz="America/New_York").tz_convert("UTC").isoformat()


def _query_result(case: dict[str, Any], status: str, *, rows: int, detail: str, sha256: str) -> dict[str, Any]:
    return {
        "symbol": case["symbol"],
        "event_date": case["event_date"],
        "control_dates": case["control_dates"],
        "dataset": case["dataset"],
        "schema": case["schema"],
        "start": case["start"],
        "end": case["end"],
        "status": status,
        "rows": rows,
        "detail": detail,
        "derived_bars_sha256": sha256,
        "raw_payload_retained": False,
    }


def _blocked_decision(reason: str, data_root: Path, output_dir: str | Path) -> dict[str, Any]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    decision = {
        "status": "blocked",
        "decision": "SEC8K_TAPE_ORACLE_DATABENTO_MINI_PANEL_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "promotion_allowed": False,
    }
    _write_json(Path(output_dir) / "final_decision.json", decision)
    _write_json(data_root / "dataset_manifest.json", {"status": "blocked", "reason": reason, "provider_query_performed": False})
    return decision


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded SEC8K Tape Oracle Databento mini-panel and backtest.")
    parser.add_argument("--max-events", type=int, default=MAX_EVENTS)
    parser.add_argument("--control-sessions", type=int, default=CONTROL_SESSIONS)
    args = parser.parse_args(argv)
    decision = run_databento_mini_panel_and_backtest(max_events=args.max_events, control_sessions=args.control_sessions)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] in {"complete", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
