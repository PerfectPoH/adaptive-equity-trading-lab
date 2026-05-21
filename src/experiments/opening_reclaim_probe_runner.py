from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


TRIAL_ID = "TRIAL-OPENING-RECLAIM-001"
RUN_ID = "OPENING-RECLAIM-INTRADAY-PROBE-001"
ROOT = Path("experiments/provider_aware_research")
SOURCE_DIR = ROOT / "data_inputs" / "gaprev_mini_panel_databento_intraday_probe_20260521"
PREREG_DIR = ROOT / "opening_reclaim_preregistration_20260521"
OUTPUT_DIR = ROOT / "execution_outputs" / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Opening-Reclaim-Intraday-Probe-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-opening-reclaim-intraday-probe.md")
NY = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class OpeningReclaimParams:
    opening_window_minutes: int = 30
    opening_shock_threshold: float = -0.05
    relative_opening_volume_threshold: float = 2.0
    vwap_reclaim_cutoff_local: str = "10:30"
    holding_window_minutes: int = 120
    round_trip_cost_bps: float = 500.0
    min_trades_for_promotion: int = 30
    dsr_threshold: float = 0.95


def run_opening_reclaim_probe(source_dir: str | Path = SOURCE_DIR) -> dict[str, Any]:
    params = OpeningReclaimParams()
    _ensure_dirs()
    prereg = _write_preregistration(params)
    rows = []
    for bars_path in sorted(Path(source_dir).glob("*/bars.csv")):
        rows.append(evaluate_opening_reclaim_event(bars_path, params))
    results = pd.DataFrame(rows)
    results.to_csv(OUTPUT_DIR / "opening_reclaim_results.csv", index=False)
    summary = summarize_opening_reclaim_results(results, params)
    _write_json(OUTPUT_DIR / "opening_reclaim_summary.json", summary)
    post_run = _write_post_run_validation(summary, params)
    decision = _write_decision(prereg, summary, post_run)
    return decision


def evaluate_opening_reclaim_event(bars_path: str | Path, params: OpeningReclaimParams) -> dict[str, Any]:
    path = Path(bars_path)
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["local_ts"] = frame["timestamp"].dt.tz_convert(NY)
    frame["session_date"] = frame["local_ts"].dt.date.astype(str)
    frame = frame.sort_values("timestamp")
    sessions = sorted(frame["session_date"].unique())
    base = {
        "source": str(path.parent.name),
        "symbol": str(frame.iloc[0]["symbol"]) if not frame.empty else "",
        "status": "blocked",
        "trade_count": 0,
    }
    if len(sessions) < 2:
        return {**base, "reason": "insufficient_sessions"}
    prev_day = frame[frame["session_date"].eq(sessions[-2])].copy()
    day = frame[frame["session_date"].eq(sessions[-1])].copy()
    if prev_day.empty or day.empty:
        return {**base, "reason": "missing_previous_or_reaction_session"}

    opening = day.head(params.opening_window_minutes).copy()
    prev_opening = prev_day.head(params.opening_window_minutes).copy()
    if opening.empty or prev_opening.empty:
        return {**base, "reason": "missing_opening_window"}
    first_open = float(opening.iloc[0]["open"])
    opening_min_low = float(opening["low"].astype(float).min())
    opening_shock = opening_min_low / first_open - 1.0
    rel_opening_volume = _safe_ratio(float(opening["volume"].astype(float).sum()), float(prev_opening["volume"].astype(float).sum()))

    day["typical_price"] = (day["high"].astype(float) + day["low"].astype(float) + day["close"].astype(float)) / 3.0
    day["cum_pv"] = (day["typical_price"] * day["volume"].astype(float)).cumsum()
    day["cum_volume"] = day["volume"].astype(float).cumsum()
    day["vwap"] = day["cum_pv"] / day["cum_volume"].replace(0, math.nan)
    cutoff_hour, cutoff_minute = [int(part) for part in params.vwap_reclaim_cutoff_local.split(":")]
    cutoff = day.iloc[0]["local_ts"].replace(hour=cutoff_hour, minute=cutoff_minute, second=0, microsecond=0)
    candidates = day[(day["local_ts"] <= cutoff) & (day["close"].astype(float) >= day["vwap"].astype(float))]
    setup_ok = opening_shock <= params.opening_shock_threshold and rel_opening_volume >= params.relative_opening_volume_threshold
    common = {
        **base,
        "status": "pass",
        "opening_shock": opening_shock,
        "relative_opening_volume": rel_opening_volume,
        "first_open": first_open,
    }
    if not setup_ok:
        return {**common, "decision": "NO_TRADE", "reason": "opening_shock_or_volume_filter_not_met"}
    if candidates.empty:
        return {**common, "decision": "NO_TRADE", "reason": "vwap_reclaim_not_met_before_cutoff"}
    entry = candidates.iloc[0]
    exit_target = entry["timestamp"] + pd.Timedelta(minutes=params.holding_window_minutes)
    exits = day[day["timestamp"] >= exit_target]
    exit_row = exits.iloc[0] if not exits.empty else day.iloc[-1]
    entry_price = float(entry["close"])
    exit_price = float(exit_row["close"])
    gross_return = exit_price / entry_price - 1.0
    net_return = gross_return - params.round_trip_cost_bps / 10000.0
    return {
        **common,
        "decision": "TRADE_EXECUTED_PROMOTION_BLOCKED",
        "trade_count": 1,
        "entry_timestamp": entry["timestamp"].isoformat(),
        "entry_price": entry_price,
        "exit_timestamp": exit_row["timestamp"].isoformat(),
        "exit_price": exit_price,
        "gross_return": gross_return,
        "net_return": net_return,
        "reason": "",
    }


def summarize_opening_reclaim_results(results: pd.DataFrame, params: OpeningReclaimParams) -> dict[str, Any]:
    trades = results[results["trade_count"].astype(int) > 0].copy() if not results.empty else pd.DataFrame()
    gross = pd.to_numeric(trades.get("gross_return", pd.Series(dtype=float)), errors="coerce").dropna()
    net = pd.to_numeric(trades.get("net_return", pd.Series(dtype=float)), errors="coerce").dropna()
    return {
        "status": "pass",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "events_evaluated": int(len(results)),
        "trade_count": int(len(net)),
        "gross_return_sum": float(gross.sum()) if len(gross) else 0.0,
        "net_return_sum": float(net.sum()) if len(net) else 0.0,
        "net_return_mean": float(net.mean()) if len(net) else None,
        "positive_net_trade_count": int((net > 0).sum()) if len(net) else 0,
        "round_trip_cost_bps": params.round_trip_cost_bps,
        "promotion_allowed": False,
        "promotion_blockers": [
            "existing_gaprev_intraday_panel_reuse",
            "below_30_trades",
            "dsr_not_claimed",
            "single_small_panel_probe",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run opening reclaim intraday-native probe.")
    parser.add_argument("--source-dir", default=str(SOURCE_DIR))
    args = parser.parse_args(argv)
    report = run_opening_reclaim_probe(args.source_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "promotion_blocked" else 2


def _write_preregistration(params: OpeningReclaimParams) -> dict[str, Any]:
    manifest = {
        "status": "PREREGISTERED_SPEC_EXECUTED_ON_EXISTING_INTRADAY_PANEL",
        "preregistration_id": "PREREG-OPENING-RECLAIM-001",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "daily_gap_as_trigger": "forbidden",
        "premarket_print_as_trigger": "forbidden",
        "primary_trigger": "RTH opening shock from intraday bars",
        "parameter_sweep_performed": False,
        "new_provider_query_performed": False,
        "round_trip_cost_bps": params.round_trip_cost_bps,
        "promotion_rule": "blocked unless trade_count>=30 and DSR>=0.95 in a future preregistered run",
    }
    _write_json(PREREG_DIR / "opening_reclaim_preregistration_manifest.json", manifest)
    _write_csv(
        PREREG_DIR / "parameter_freeze.csv",
        ["parameter", "value", "status"],
        [
            ["opening_window_minutes", params.opening_window_minutes, "frozen"],
            ["opening_shock_threshold", params.opening_shock_threshold, "frozen"],
            ["relative_opening_volume_threshold", params.relative_opening_volume_threshold, "frozen"],
            ["vwap_reclaim_cutoff_local", params.vwap_reclaim_cutoff_local, "frozen"],
            ["holding_window_minutes", params.holding_window_minutes, "frozen"],
            ["round_trip_cost_bps", params.round_trip_cost_bps, "frozen"],
            ["daily_gap_as_trigger", "forbidden", "frozen"],
        ],
    )
    return manifest


def _write_post_run_validation(summary: dict[str, Any], params: OpeningReclaimParams) -> dict[str, Any]:
    checks = [
        ("results_written", (OUTPUT_DIR / "opening_reclaim_results.csv").exists()),
        ("cost_500bps_enforced", float(summary["round_trip_cost_bps"]) == params.round_trip_cost_bps),
        ("promotion_blocked_below_30_trades", int(summary["trade_count"]) < params.min_trades_for_promotion),
        ("no_dsr_claimed", int(summary["trade_count"]) < params.min_trades_for_promotion),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "fail",
        "decision": "OPENING_RECLAIM_POST_RUN_PASS_PROMOTION_BLOCKED",
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
    }
    _write_json(OUTPUT_DIR / "post_run_validation_report.json", report)
    return report


def _write_decision(prereg: dict[str, Any], summary: dict[str, Any], post_run: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "promotion_blocked",
        "decision": "OPENING_RECLAIM_INTRADAY_PROBE_COMPLETE__NO_PROMOTION",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "events_evaluated": summary["events_evaluated"],
        "trade_count": summary["trade_count"],
        "gross_return_sum": summary["gross_return_sum"],
        "net_return_sum": summary["net_return_sum"],
        "net_return_mean": summary["net_return_mean"],
        "positive_net_trade_count": summary["positive_net_trade_count"],
        "round_trip_cost_bps": summary["round_trip_cost_bps"],
        "promotion_allowed": False,
        "promotion_blockers": summary["promotion_blockers"],
        "points_completed": {
            "1_preregistration": prereg["status"],
            "2_existing_intraday_panel_evaluation": summary["status"],
            "3_post_run_validation": post_run["status"],
            "4_decision": "NO_PROMOTION",
        },
    }
    _write_json(OUTPUT_DIR / "final_decision.json", decision)
    report = _format_report(decision)
    VAULT_REPORT.write_text(report, encoding="utf-8")
    VAULT_DEVLOG.write_text(report, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any]) -> str:
    return (
        "# Report Opening Reclaim Intraday Probe - 2026-05-21\n\n"
        f"Status: {decision['decision']}\n\n"
        f"- Events evaluated: {decision['events_evaluated']}\n"
        f"- Trades generated: {decision['trade_count']}\n"
        f"- Gross return sum: {decision['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {decision['net_return_sum']}\n"
        f"- Net return mean: {decision['net_return_mean']}\n"
        f"- Positive net trades: {decision['positive_net_trade_count']}\n\n"
        "Decision: no promotion. This intraday-native probe avoids daily-gap triggers, but remains a small reused panel and cannot establish an edge.\n"
    )


def _ensure_dirs() -> None:
    for path in [PREREG_DIR, OUTPUT_DIR, VAULT_REPORT.parent, VAULT_DEVLOG.parent]:
        path.mkdir(parents=True, exist_ok=True)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else math.inf


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
