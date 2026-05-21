from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import date, datetime, time
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
RUN_ID = "GAPREV-MINI-PANEL-PROBE-001"
ROOT = Path("experiments/provider_aware_research")
SOURCE_DAILY = ROOT / "data_inputs" / "databento_xmom_20260520" / "prices.csv"
PANEL_GATE_DIR = ROOT / "gaprev_mini_panel_event_gate_20260521"
PROBE_APPROVAL_DIR = ROOT / "gaprev_mini_panel_probe_approval_20260521"
DATA_DIR = ROOT / "data_inputs" / "gaprev_mini_panel_databento_intraday_probe_20260521"
OUTPUT_DIR = ROOT / "execution_outputs" / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-GapRev-Mini-Panel-Probe-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-gaprev-mini-panel-probe.md")
NY = ZoneInfo("America/New_York")


def run_gaprev_mini_panel_probe(panel_size: int = 15) -> dict[str, Any]:
    _ensure_dirs()
    params = GapRevParameters()
    candidates = select_gaprev_mini_panel_candidates(SOURCE_DAILY, panel_size=panel_size)
    gate = _write_panel_gate(candidates, panel_size)
    approval = _write_probe_approval(candidates)
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(_probe_and_replay_candidate(candidate, params))
    results = pd.DataFrame(rows)
    results_path = OUTPUT_DIR / "mini_panel_results.csv"
    results.to_csv(results_path, index=False)
    summary = _summarize_results(results, params)
    _write_json(OUTPUT_DIR / "mini_panel_summary.json", summary)
    post_run = _write_post_run_validation(results, summary, params)
    decision = _write_decision(gate, approval, summary, post_run)
    return decision


def select_gaprev_mini_panel_candidates(source_daily: str | Path, panel_size: int = 15) -> list[dict[str, Any]]:
    frame = pd.read_csv(source_daily).sort_values(["symbol", "date"])
    frame = frame[frame["symbol"].astype(str) != "IWM"].copy()
    frame["prev_close"] = frame.groupby("symbol")["close"].shift(1)
    frame["daily_gap"] = frame["open"] / frame["prev_close"] - 1.0
    frame["adv20"] = frame.groupby("symbol")["volume"].transform(lambda series: series.shift(1).rolling(20, min_periods=10).mean())
    frame["daily_relative_volume"] = frame["volume"] / frame["adv20"]
    eligible = frame[(frame["daily_gap"] <= -0.05) & (frame["daily_relative_volume"] >= 2.0)].copy()
    eligible = eligible[~((eligible["symbol"] == "CRMD") & (eligible["date"] == "2025-05-06"))]
    eligible = eligible.sort_values(["daily_relative_volume", "daily_gap"], ascending=[False, True]).head(panel_size)
    candidates: list[dict[str, Any]] = []
    for _, row in eligible.iterrows():
        event_date = str(row["date"])
        symbol = str(row["symbol"])
        candidates.append(
            {
                "symbol": symbol,
                "event_date": event_date,
                "previous_date": _previous_available_date(frame, symbol, event_date),
                "provider_dataset": str(row["provider_dataset"]),
                "daily_open": float(row["open"]),
                "daily_prev_close": float(row["prev_close"]),
                "daily_gap": float(row["daily_gap"]),
                "daily_volume": int(row["volume"]),
                "daily_adv20": float(row["adv20"]),
                "daily_relative_volume": float(row["daily_relative_volume"]),
            }
        )
    return candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GAPREV mini-panel controlled probe.")
    parser.add_argument("--panel-size", type=int, default=15)
    args = parser.parse_args(argv)
    report = run_gaprev_mini_panel_probe(panel_size=args.panel_size)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "promotion_blocked" else 2


def _ensure_dirs() -> None:
    for path in [PANEL_GATE_DIR, PROBE_APPROVAL_DIR, DATA_DIR, OUTPUT_DIR, VAULT_REPORT.parent, VAULT_DEVLOG.parent]:
        path.mkdir(parents=True, exist_ok=True)


def _write_panel_gate(candidates: list[dict[str, Any]], panel_size: int) -> dict[str, Any]:
    manifest = {
        "status": "MINI_PANEL_SELECTED_FOR_CONTROLLED_PROBE",
        "gate_id": "GAPREV-MINI-PANEL-EVENT-GATE-001",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "source_daily_file": str(SOURCE_DAILY),
        "panel_size_requested": panel_size,
        "panel_size_selected": len(candidates),
        "selection_rule": "daily_gap<=-5pct AND daily_relative_volume>=2x; exclude CRMD 2025-05-06 false RTH-open case; rank by daily_relative_volume desc",
        "pnl_intraday_observed_before_selection": False,
        "parameter_sweep_performed": False,
        "round_trip_cost_bps_locked": 500.0,
        "strategy_promotion_authorized": False,
    }
    _write_json(PANEL_GATE_DIR / "mini_panel_event_gate_manifest.json", manifest)
    _write_csv(PANEL_GATE_DIR / "selected_candidates.csv", list(candidates[0].keys()), [[candidate[key] for key in candidate] for candidate in candidates])
    return manifest


def _write_probe_approval(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = {
        "status": "APPROVED_MINI_PANEL_PROVIDER_PROBE",
        "gate_id": "GAPREV-MINI-PANEL-PROBE-APPROVAL-001",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "provider": "Databento Historical",
        "schema": "ohlcv-1m",
        "candidate_count": len(candidates),
        "max_provider_calls": len(candidates),
        "raw_payload_retention_allowed": False,
        "derived_bars_retention_allowed": True,
    }
    _write_json(PROBE_APPROVAL_DIR / "mini_panel_probe_approval_manifest.json", manifest)
    _write_csv(
        PROBE_APPROVAL_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["parameter_sweep", "blocked", "Frozen GapRev parameters only."],
            ["save_raw_payload", "blocked", "Derived bars only."],
            ["expand_beyond_selected_panel", "blocked", "Panel fixed before provider calls."],
            ["strategy_promotion", "blocked", "Mini-panel remains below promotion sample-size gate."],
        ],
    )
    return manifest


def _probe_and_replay_candidate(candidate: dict[str, Any], params: GapRevParameters) -> dict[str, Any]:
    symbol = candidate["symbol"]
    event_date = candidate["event_date"]
    event_dir = DATA_DIR / f"{symbol}_{event_date}"
    event_dir.mkdir(parents=True, exist_ok=True)
    start, end = _utc_query_bounds(candidate["previous_date"], event_date)
    base = {
        "symbol": symbol,
        "event_date": event_date,
        "previous_date": candidate["previous_date"],
        "daily_gap": candidate["daily_gap"],
        "daily_relative_volume": candidate["daily_relative_volume"],
        "provider_dataset": candidate["provider_dataset"],
        "start": start,
        "end": end,
    }
    try:
        import databento as db
    except Exception as exc:  # pragma: no cover
        return {**base, "status": "provider_blocked", "reason": f"databento_package_unavailable:{type(exc).__name__}", "trade_count": 0}
    api_key = _load_databento_key()
    if not api_key:
        return {**base, "status": "provider_blocked", "reason": "databento_api_key_missing", "trade_count": 0}
    try:
        client = db.Historical(api_key)
        data = client.timeseries.get_range(
            dataset=candidate["provider_dataset"],
            symbols=[symbol],
            schema="ohlcv-1m",
            start=start,
            end=end,
            limit=1000,
        )
        frame = data.to_df().reset_index()
    except Exception as exc:  # pragma: no cover
        return {**base, "status": "provider_error", "reason": f"{type(exc).__name__}:{str(exc)[:180]}", "trade_count": 0}
    bars = pd.DataFrame(
        {
            "symbol": frame["symbol"].astype(str),
            "timestamp": pd.to_datetime(frame["ts_event"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": frame["open"].astype(float),
            "high": frame["high"].astype(float),
            "low": frame["low"].astype(float),
            "close": frame["close"].astype(float),
            "volume": frame["volume"].astype(int),
            "provider_dataset": candidate["provider_dataset"],
            "schema": "ohlcv-1m",
        }
    ).sort_values("timestamp")
    bars = _filter_regular_trading_hours(bars)
    bars_path = event_dir / "bars.csv"
    bars.to_csv(bars_path, index=False)
    validation = validate_intraday_bars(bars_path)
    data_manifest = {
        **base,
        "status": "pass" if validation["status"] == "pass" else "fail",
        "rows": int(len(bars)),
        "raw_payload_retained": False,
        "derived_bars_sha256": _sha256(bars_path),
        "validation_status": validation["status"],
    }
    _write_json(event_dir / "data_input_manifest.json", data_manifest)
    _write_json(event_dir / "data_input_validation_report.json", validation)
    if validation["status"] != "pass":
        return {**base, "status": "data_validation_fail", "reason": "intraday_bars_contract_failed", "trade_count": 0}
    replay = controlled_backtest_from_frame(bars, params)
    replay["run_id"] = RUN_ID
    _write_json(event_dir / "controlled_backtest_result.json", replay)
    return {
        **base,
        "status": replay.get("status"),
        "decision": replay.get("decision"),
        "trade_count": int(replay.get("trade_count", 0)),
        "rth_gap_return": replay.get("gap_return"),
        "relative_opening_volume": replay.get("relative_opening_volume"),
        "entry_price": replay.get("entry_price"),
        "exit_price": replay.get("exit_price"),
        "gross_return": replay.get("gross_return"),
        "net_return": replay.get("net_return"),
        "reason": replay.get("reason", ""),
        "rows": int(len(bars)),
    }


def _summarize_results(results: pd.DataFrame, params: GapRevParameters) -> dict[str, Any]:
    executed = results[results["trade_count"].astype(int) > 0].copy()
    net_returns = pd.to_numeric(executed.get("net_return", pd.Series(dtype=float)), errors="coerce").dropna()
    gross_returns = pd.to_numeric(executed.get("gross_return", pd.Series(dtype=float)), errors="coerce").dropna()
    return {
        "status": "pass",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "events_selected": int(len(results)),
        "events_with_data": int((results["status"].astype(str) == "pass").sum()),
        "trade_count": int(len(net_returns)),
        "gross_return_sum": float(gross_returns.sum()) if len(gross_returns) else 0.0,
        "net_return_sum": float(net_returns.sum()) if len(net_returns) else 0.0,
        "net_return_mean": float(net_returns.mean()) if len(net_returns) else None,
        "positive_net_trade_count": int((net_returns > 0).sum()) if len(net_returns) else 0,
        "round_trip_cost_bps": params.round_trip_cost_bps,
        "promotion_allowed": False,
        "promotion_blockers": [
            "mini_panel_below_30_trades",
            "dsr_not_valid_for_small_sample",
            "known_forensic_universe",
        ],
    }


def _write_post_run_validation(results: pd.DataFrame, summary: dict[str, Any], params: GapRevParameters) -> dict[str, Any]:
    checks = [
        ("results_file_written", (OUTPUT_DIR / "mini_panel_results.csv").exists()),
        ("panel_has_at_least_one_event", int(summary["events_selected"]) > 0),
        ("round_trip_cost_500bps_enforced", float(summary["round_trip_cost_bps"]) == params.round_trip_cost_bps),
        ("promotion_blocked_below_30_trades", int(summary["trade_count"]) < params.min_trades_for_promotion),
        ("no_dsr_claim_for_small_sample", int(summary["trade_count"]) < params.min_trades_for_promotion),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "fail",
        "decision": "GAPREV_MINI_PANEL_POST_RUN_PASS_PROMOTION_BLOCKED",
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
    }
    _write_json(OUTPUT_DIR / "post_run_validation_report.json", report)
    return report


def _write_decision(gate: dict[str, Any], approval: dict[str, Any], summary: dict[str, Any], post_run: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "promotion_blocked",
        "decision": "MINI_PANEL_COMPLETE__NO_PROMOTION",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "events_selected": summary["events_selected"],
        "trade_count": summary["trade_count"],
        "gross_return_sum": summary["gross_return_sum"],
        "net_return_sum": summary["net_return_sum"],
        "net_return_mean": summary["net_return_mean"],
        "positive_net_trade_count": summary["positive_net_trade_count"],
        "round_trip_cost_bps": summary["round_trip_cost_bps"],
        "promotion_allowed": False,
        "promotion_blockers": summary["promotion_blockers"],
        "points_completed": {
            "1_mini_panel_event_gate": gate["status"],
            "2_probe_approval": approval["status"],
            "3_intraday_data_ingestion_and_replay": summary["status"],
            "4_post_run_validation": post_run["status"],
            "5_decision": "NO_PROMOTION",
        },
    }
    _write_json(OUTPUT_DIR / "final_decision.json", decision)
    report = _format_report(decision)
    VAULT_REPORT.write_text(report, encoding="utf-8")
    VAULT_DEVLOG.write_text(report, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any]) -> str:
    return (
        "# Report GAPREV Mini-Panel Probe - 2026-05-21\n\n"
        f"Status: {decision['decision']}\n\n"
        f"- Events selected: {decision['events_selected']}\n"
        f"- Trades generated: {decision['trade_count']}\n"
        f"- Gross return sum: {decision['gross_return_sum']}\n"
        f"- Net return sum after 500 bps per trade: {decision['net_return_sum']}\n"
        f"- Net return mean: {decision['net_return_mean']}\n"
        f"- Positive net trades: {decision['positive_net_trade_count']}\n\n"
        "Decision: no promotion. The mini-panel remains below the 30-trade promotion gate and DSR is not claimed.\n"
    )


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
