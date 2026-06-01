from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


PANEL_PATH = Path(
    "experiments/provider_aware_research/public_catalyst_hybrid_event_panel_run_20260601/hybrid_event_panel.csv"
)
OUTPUT_DIR = Path(
    "experiments/provider_aware_research/execution_outputs/PUBLIC-CATALYST-HYBRID-MICRO-BACKTEST-001"
)
WINDOWS = (30, 60, 90)


def build_micro_backtest(
    events: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    *,
    windows: Iterable[int] = WINDOWS,
    cost_bps: int = 500,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, event in events.iterrows():
        if str(event.get("admissibility_label")) != "admissible_event":
            continue
        if str(event.get("pit_proof_status")) != "pass":
            continue
        symbol = str(event.get("symbol", "")).strip()
        frame = _normalise_price_frame(frames.get(symbol))
        if frame is None or frame.empty:
            continue
        event_date = pd.Timestamp(str(event["event_date"])).normalize()
        for window in windows:
            trade = _trade_for_event(event, frame, event_date, int(window), cost_bps=cost_bps)
            if trade:
                rows.append(trade)
    return rows


def summarize_micro_backtest(
    trades: list[dict[str, Any]],
    *,
    event_count: int,
    minimum_price_covered_events: int = 8,
) -> dict[str, Any]:
    trade_frame = pd.DataFrame(trades)
    covered_events = sorted(set(trade_frame["event_id"].astype(str))) if not trade_frame.empty else []
    blockers = [
        "manual_panel_non_promotable",
        "coverage_completeness_not_proven",
        "delisted_retention_not_proven",
    ]
    if len(covered_events) < minimum_price_covered_events:
        blockers.append(f"price_covered_events_below_{minimum_price_covered_events}")
    decision = (
        "PUBLIC_CATALYST_HYBRID_MICRO_BACKTEST_ARCHIVE_SAMPLE_STARVED"
        if len(covered_events) < minimum_price_covered_events
        else "PUBLIC_CATALYST_HYBRID_MICRO_BACKTEST_COMPLETE_EXPLORATORY_ONLY"
    )
    if trade_frame.empty:
        by_window: dict[str, Any] = {}
        total_weighted_net = 0.0
        win_rate = 0.0
        max_drawdown = 0.0
    else:
        by_window = {
            str(window): {
                "trade_count": int(len(group)),
                "gross_return_sum": float(group["gross_return"].sum()),
                "net_return_sum": float(group["net_return"].sum()),
                "median_net_return": float(group["net_return"].median()),
                "win_rate": float((group["net_return"] > 0).mean()),
            }
            for window, group in trade_frame.groupby("window_days")
        }
        total_weighted_net = float(trade_frame["weighted_net_return"].sum())
        win_rate = float((trade_frame["net_return"] > 0).mean())
        max_drawdown = _max_drawdown(trade_frame)
    return {
        "decision": decision,
        "event_count": int(event_count),
        "price_covered_event_count": len(covered_events),
        "trade_count": int(len(trade_frame)),
        "windows": list(WINDOWS),
        "weighted_net_return_sum": total_weighted_net,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "by_window": by_window,
        "blockers": blockers,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "parameter_sweep_performed": False,
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "backtest_performed": True,
        "financial_performance_claimed": False,
    }


def load_norgate_local_frames(symbols: Iterable[str], *, min_rows: int = 20) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    import norgatedata

    frames: dict[str, pd.DataFrame] = {}
    failures: dict[str, str] = {}
    for symbol in sorted(set(str(item).strip() for item in symbols if str(item).strip())):
        try:
            frame = norgatedata.price_timeseries(symbol, timeseriesformat="pandas-dataframe")
        except Exception as exc:  # pragma: no cover - depends on local Norgate installation
            failures[symbol] = type(exc).__name__
            continue
        normalised = _normalise_price_frame(frame)
        if normalised is None or len(normalised) < min_rows:
            failures[symbol] = "insufficient_local_price_history"
            continue
        frames[symbol] = normalised
    return frames, {
        "source": "local_norgate_database",
        "market_data_download_performed": False,
        "provider_query_performed": False,
        "loaded_symbols": sorted(frames),
        "failures": failures,
    }


def run_public_catalyst_hybrid_micro_backtest(
    *,
    panel_path: str | Path = PANEL_PATH,
    output_dir: str | Path = OUTPUT_DIR,
    cost_bps: int = 500,
    minimum_price_covered_events: int = 8,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(panel_path)
    frames, price_manifest = load_norgate_local_frames(events["symbol"].astype(str).tolist())
    trades = build_micro_backtest(events, frames, windows=WINDOWS, cost_bps=cost_bps)
    summary = summarize_micro_backtest(
        trades,
        event_count=len(events),
        minimum_price_covered_events=minimum_price_covered_events,
    )
    decision = {
        "decision": summary["decision"],
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "backtest_performed": True,
        "price_manifest": price_manifest,
        "summary": summary,
    }
    _write_csv(output / "trade_log.csv", trades)
    _write_json(output / "diagnostic_summary.json", summary)
    _write_json(output / "price_manifest.json", price_manifest)
    _write_json(output / "final_decision.json", decision)
    (output / "micro_backtest_report.md").write_text(_report(summary, price_manifest), encoding="utf-8")
    return decision


def _trade_for_event(
    event: pd.Series,
    frame: pd.DataFrame,
    event_date: pd.Timestamp,
    window: int,
    *,
    cost_bps: int,
) -> dict[str, Any] | None:
    event_pos = frame.index.searchsorted(event_date, side="left")
    if event_pos >= len(frame):
        return None
    exit_pos = max(0, event_pos - 1)
    entry_pos = exit_pos - window
    if entry_pos < 0:
        return None
    entry_date = frame.index[entry_pos]
    exit_date = frame.index[exit_pos]
    entry_price = float(frame.loc[entry_date, "Open"])
    exit_price = float(frame.loc[exit_date, "Close"])
    if entry_price <= 0 or exit_price <= 0:
        return None
    gross = exit_price / entry_price - 1.0
    cost = cost_bps / 10_000.0
    net = gross - cost
    return {
        "event_id": str(event["event_id"]),
        "symbol": str(event["symbol"]),
        "event_date": event_date.date().isoformat(),
        "window_days": int(window),
        "entry_date": entry_date.date().isoformat(),
        "exit_date": exit_date.date().isoformat(),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "gross_return": gross,
        "cost_return": cost,
        "net_return": net,
        "weighted_net_return": net / len(WINDOWS),
        "outcome_status": str(event.get("outcome_status", "unknown")),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "short_selling_allowed": False,
    }


def _normalise_price_frame(frame: pd.DataFrame | None) -> pd.DataFrame | None:
    if frame is None or frame.empty:
        return None
    data = frame.copy()
    data.index = pd.to_datetime(data.index).tz_localize(None).normalize()
    required = {"Open", "Close"}
    if not required.issubset(data.columns):
        return None
    return data.sort_index()


def _max_drawdown(trade_frame: pd.DataFrame) -> float:
    curve = trade_frame.copy()
    curve["date"] = pd.to_datetime(curve["exit_date"])
    grouped = curve.groupby("date")["weighted_net_return"].sum().sort_index().cumsum()
    drawdown = grouped - grouped.cummax()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _report(summary: dict[str, Any], price_manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Public Catalyst Hybrid Micro-Backtest 001",
            "",
            f"- decision: `{summary['decision']}`",
            f"- events in panel: `{summary['event_count']}`",
            f"- events with local price coverage: `{summary['price_covered_event_count']}`",
            f"- trades: `{summary['trade_count']}`",
            f"- weighted net return sum: `{summary['weighted_net_return_sum']:.6f}`",
            f"- win rate: `{summary['win_rate']:.4f}`",
            f"- max drawdown: `{summary['max_drawdown']:.6f}`",
            f"- loaded local symbols: `{len(price_manifest.get('loaded_symbols', []))}`",
            f"- price failures: `{len(price_manifest.get('failures', {}))}`",
            "",
            "## Blockers",
            "",
            *[f"- `{blocker}`" for blocker in summary.get("blockers", [])],
            "",
            "This is exploratory only. No promotion, paper trading, live trading, or durable performance claim is allowed.",
        ]
    )
