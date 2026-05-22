from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd


RUN_ID = "SEC-8K-XMOM-OVERLAP-DIAGNOSTIC-001"
TRIAL_ID = "TRIAL-SEC8K-XMOM-OVERLAP-DIAGNOSTIC-001"
ROOT = Path("experiments/provider_aware_research")
TRADE_LOG = Path("experiments/runs/xmom_trial_001_20260520/portfolio_trade_log.csv")
PRICE_FILE = ROOT / "data_inputs" / "databento_xmom_20260520" / "prices.csv"
EVENT_PANEL = ROOT / "sec_8k_multisymbol_event_timing_diagnostic_20260522" / "sec_8k_multisymbol_event_panel.csv"
ARTIFACT_DIR = ROOT / "sec_8k_xmom_overlap_diagnostic_20260522"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC8K-XMOM-Overlap-Diagnostic-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-sec8k-xmom-overlap-diagnostic.md")


def run_sec8k_xmom_overlap_diagnostic(
    trade_log: str | Path = TRADE_LOG,
    price_file: str | Path = PRICE_FILE,
    event_panel: str | Path = EVENT_PANEL,
    window_days: int = 5,
) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(trade_log)
    prices = pd.read_csv(price_file)
    events = pd.read_csv(event_panel)
    panel = build_overlap_panel(trades, prices, events, window_days=window_days)
    _write_csv(ARTIFACT_DIR / "sec8k_xmom_overlap_panel.csv", list(panel[0].keys()) if panel else [], panel)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    summary = summarize_overlap_panel(panel, window_days=window_days)
    _write_json(ARTIFACT_DIR / "diagnostic_summary.json", summary)
    decision = write_final_decision(summary)
    write_vault_report(summary, decision, panel)
    return decision


def build_overlap_panel(trades: pd.DataFrame, prices: pd.DataFrame, events: pd.DataFrame, window_days: int) -> list[dict[str, Any]]:
    calendars = build_symbol_calendars(prices)
    event_index = build_event_index(events)
    rows: list[dict[str, Any]] = []
    for _, trade in trades.iterrows():
        symbol = str(trade["symbol"])
        calendar = calendars.get(symbol, [])
        symbol_events = event_index.get(symbol, [])
        overlap = nearest_event_overlap(
            calendar=calendar,
            event_dates=symbol_events,
            signal_date=str(trade["signal_date"]),
            entry_date=str(trade["entry_date"]),
            exit_date=str(trade["exit_date"]),
            window_days=window_days,
        )
        pnl = float(trade["pnl"])
        rows.append(
            {
                "symbol": symbol,
                "signal_date": str(trade["signal_date"]),
                "entry_date": str(trade["entry_date"]),
                "exit_date": str(trade["exit_date"]),
                "pnl": round(pnl, 6),
                "return_pct": round(float(trade["return_pct"]), 10),
                "winner_label": "winner" if pnl > 0 else "loser",
                "is_top3_winner": False,
                "overlaps_sec8k_window": overlap["overlaps_sec8k_window"],
                "nearest_event_date": overlap["nearest_event_date"],
                "nearest_event_anchor": overlap["nearest_event_anchor"],
                "nearest_event_distance_trading_days": overlap["nearest_event_distance_trading_days"],
                "window_days": window_days,
            }
        )
    top_indices = sorted(range(len(rows)), key=lambda idx: rows[idx]["pnl"], reverse=True)[:3]
    for idx in top_indices:
        rows[idx]["is_top3_winner"] = True
    return rows


def build_symbol_calendars(prices: pd.DataFrame) -> dict[str, list[str]]:
    calendars: dict[str, list[str]] = {}
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.date.astype(str)
    for symbol, group in frame.groupby("symbol"):
        calendars[str(symbol)] = sorted(str(value) for value in group["date"].unique())
    return calendars


def build_event_index(events: pd.DataFrame) -> dict[str, list[str]]:
    frame = events[events.get("status", pd.Series(dtype=str)).astype(str).eq("event")].copy()
    index: dict[str, list[str]] = {}
    for symbol, group in frame.groupby("symbol"):
        index[str(symbol)] = sorted(str(value) for value in group["reaction_session_date"].dropna().unique())
    return index


def nearest_event_overlap(
    *,
    calendar: list[str],
    event_dates: list[str],
    signal_date: str,
    entry_date: str,
    exit_date: str,
    window_days: int,
) -> dict[str, Any]:
    if not calendar or not event_dates:
        return _empty_overlap()
    positions = {day: idx for idx, day in enumerate(calendar)}
    anchors = {"signal": signal_date, "entry": entry_date, "exit": exit_date}
    event_positions = [(event, positions[event]) for event in event_dates if event in positions]
    best: dict[str, Any] | None = None
    for anchor_name, anchor_date in anchors.items():
        if anchor_date not in positions:
            continue
        anchor_pos = positions[anchor_date]
        for event_date, event_pos in event_positions:
            distance = anchor_pos - event_pos
            abs_distance = abs(distance)
            if best is None or abs_distance < best["abs_distance"]:
                best = {
                    "nearest_event_date": event_date,
                    "nearest_event_anchor": anchor_name,
                    "nearest_event_distance_trading_days": distance,
                    "abs_distance": abs_distance,
                }
    if best is None:
        return _empty_overlap()
    return {
        "overlaps_sec8k_window": best["abs_distance"] <= window_days,
        "nearest_event_date": best["nearest_event_date"],
        "nearest_event_anchor": best["nearest_event_anchor"],
        "nearest_event_distance_trading_days": best["nearest_event_distance_trading_days"],
    }


def summarize_overlap_panel(rows: list[dict[str, Any]], window_days: int) -> dict[str, Any]:
    overlapped = [row for row in rows if row["overlaps_sec8k_window"] is True]
    outside = [row for row in rows if row["overlaps_sec8k_window"] is False]
    winners = [row for row in rows if row["winner_label"] == "winner"]
    losers = [row for row in rows if row["winner_label"] == "loser"]
    top3 = [row for row in rows if row["is_top3_winner"] is True]
    overlap_rate = len(overlapped) / len(rows) if rows else 0.0
    winner_overlap_rate = _rate(winners, "overlaps_sec8k_window")
    loser_overlap_rate = _rate(losers, "overlaps_sec8k_window")
    top3_overlap_rate = _rate(top3, "overlaps_sec8k_window")
    blockers: list[str] = []
    if len(rows) < 30:
        blockers.append("trade_count_below_30")
    if top3_overlap_rate < 2 / 3:
        blockers.append("top3_winners_not_concentrated_in_sec8k_windows")
    if winner_overlap_rate <= loser_overlap_rate:
        blockers.append("winner_overlap_not_above_loser_overlap")
    decision = "SEC8K_XMOM_OVERLAP_SUPPORTS_CATALYST_EXPLANATION" if len(blockers) == 1 and blockers[0] == "trade_count_below_30" else "SEC8K_XMOM_OVERLAP_DIAGNOSTIC_ARCHIVE_CURRENT_FORM"
    return {
        "status": "diagnostic_complete_existing_artifacts_only",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "window_days": window_days,
        "trade_count": len(rows),
        "overlap_count": len(overlapped),
        "overlap_rate": round(overlap_rate, 6),
        "winner_overlap_rate": round(winner_overlap_rate, 6),
        "loser_overlap_rate": round(loser_overlap_rate, 6),
        "top3_winner_overlap_rate": round(top3_overlap_rate, 6),
        "overlap_median_pnl": round(_median_pnl(overlapped), 6),
        "outside_median_pnl": round(_median_pnl(outside), 6),
        "overlap_total_pnl": round(sum(float(row["pnl"]) for row in overlapped), 6),
        "outside_total_pnl": round(sum(float(row["pnl"]) for row in outside), 6),
        "promotion_allowed": False,
        "blockers": blockers,
        "provider_query_performed": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def write_final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "trade_count": summary["trade_count"],
        "overlap_rate": summary["overlap_rate"],
        "top3_winner_overlap_rate": summary["top3_winner_overlap_rate"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If overlap supports catalyst explanation, preregister SEC8K direction-source study; do not use overlap as a trading filter.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    return decision


def validate_sec8k_xmom_overlap_diagnostic(diag_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(diag_dir)
    checks: list[dict[str, Any]] = []
    required = ["sec8k_xmom_overlap_panel.csv", "blocked_actions.csv", "diagnostic_summary.json", "final_decision.json"]
    _check(checks, "diagnostic_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    panel = _read_csv(path / "sec8k_xmom_overlap_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(panel[0].keys()) if panel else set()
    required_cols = {"symbol", "signal_date", "pnl", "overlaps_sec8k_window", "nearest_event_date", "is_top3_winner"}
    forbidden_cols = {"sharpe", "dsr", "optimized_threshold", "paper_signal", "live_signal"}
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "required_columns_present", required_cols.issubset(columns), f"missing={sorted(required_cols - columns)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked")
    _check(checks, "summary_no_execution", summary.get("provider_query_performed") is False and summary.get("backtest_performed") is False, str(summary))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision))
    return _report(checks)


def write_vault_report(summary: dict[str, Any], decision: dict[str, Any], panel: list[dict[str, Any]]) -> None:
    rows = "\n".join(
        f"- {row['symbol']} signal={row['signal_date']} pnl={row['pnl']} overlap={row['overlaps_sec8k_window']} "
        f"event={row['nearest_event_date']} anchor={row['nearest_event_anchor']} dist={row['nearest_event_distance_trading_days']} top3={row['is_top3_winner']}"
        for row in panel
    )
    text = (
        "# Report SEC8K XMOM Overlap Diagnostic - 2026-05-22\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Diagnostic-only overlap between XMOM-001 trades and SEC 8-K Item 2.02 reaction-session windows. "
        "No provider query, new backtest, parameter sweep, paper/live trading or promotion was performed.\n\n"
        "## Result\n\n"
        f"- Trade count: {summary['trade_count']}\n"
        f"- Window days: +/-{summary['window_days']} trading days\n"
        f"- Overlap count: {summary['overlap_count']}\n"
        f"- Overlap rate: {summary['overlap_rate']}\n"
        f"- Winner overlap rate: {summary['winner_overlap_rate']}\n"
        f"- Loser overlap rate: {summary['loser_overlap_rate']}\n"
        f"- Top3 winner overlap rate: {summary['top3_winner_overlap_rate']}\n"
        f"- Overlap median PnL: {summary['overlap_median_pnl']}\n"
        f"- Outside median PnL: {summary['outside_median_pnl']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Panel\n\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "This diagnostic asks whether XMOM was accidentally exposed to SEC 8-K regimes. It is historical interpretation only and must not be used as a trading filter without a separate preregistration.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC8K/XMOM overlap diagnostic.")
    parser.add_argument("--trade-log", default=str(TRADE_LOG))
    parser.add_argument("--price-file", default=str(PRICE_FILE))
    parser.add_argument("--event-panel", default=str(EVENT_PANEL))
    parser.add_argument("--window-days", type=int, default=5)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_sec8k_xmom_overlap_diagnostic(args.trade_log, args.price_file, args.event_panel, args.window_days)
    report = validate_sec8k_xmom_overlap_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Overlap uses existing SEC event panel."],
        ["run_backtest", "blocked", "Diagnostic uses existing XMOM trade log only."],
        ["use_overlap_as_filter", "blocked", "Would be post-hoc interpretation unless separately preregistered."],
        ["parameter_sweep_window", "blocked", "Window is fixed at diagnostic start."],
        ["paper_trading", "blocked", "No strategy has been promoted."],
        ["live_trading", "blocked", "No strategy has been promoted."],
    ]


def _empty_overlap() -> dict[str, Any]:
    return {
        "overlaps_sec8k_window": False,
        "nearest_event_date": "",
        "nearest_event_anchor": "",
        "nearest_event_distance_trading_days": "",
    }


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row[key] is True) / len(rows)


def _median_pnl(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return median(float(row["pnl"]) for row in rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]] | list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if rows and isinstance(rows[0], dict):
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)  # type: ignore[arg-type]
        else:
            writer = csv.writer(handle)
            writer.writerow(fieldnames)
            writer.writerows(rows)  # type: ignore[arg-type]


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC8K_XMOM_OVERLAP_DIAGNOSTIC_PASS" if failed == 0 else "SEC8K_XMOM_OVERLAP_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
