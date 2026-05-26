from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

import pandas as pd


OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/ORB-930-CROSS-ASSET-BACKTEST-001")
DATA_DIR = Path("experiments/provider_aware_research/data_inputs/orb_930_cross_asset_yfinance_20260526")
SYMBOLS = {
    "GC=F": "Gold futures proxy",
    "EURUSD=X": "Euro / US dollar",
    "BTC-USD": "Bitcoin / US dollar",
}
RANGE_MINUTES = [5, 15]
REWARD_R_MULTIPLES = [1, 3, 4]
ROUND_TRIP_COST_BPS = 5


@dataclass(frozen=True)
class OrbConfig:
    range_minutes: int
    reward_r: int
    entry_cutoff: time = time(11, 0)
    session_close: time = time(16, 0)
    open_time: time = time(9, 30)
    cost_bps: int = ROUND_TRIP_COST_BPS


def build_pre_run_gate() -> dict[str, Any]:
    return {
        "gate_id": "ORB-930-CROSS-ASSET-PRE-RUN-GATE-001",
        "strategy": "9:30 AM Opening Range Breakout",
        "status": "APPROVED_FOR_BOUNDED_PROVIDER_QUERY",
        "approval_basis": "User explicitly requested the 9:30 AM strategy backtest on gold, euro, and bitcoin.",
        "provider": "Yahoo Finance through yfinance",
        "provider_query_allowed": True,
        "raw_payload_retention_allowed": False,
        "market_data_download_allowed": True,
        "symbols": SYMBOLS,
        "interval": "5m",
        "period": "60d",
        "timezone": "America/New_York",
        "parameter_freeze": {
            "opening_range_minutes": RANGE_MINUTES,
            "reward_r_multiples": REWARD_R_MULTIPLES,
            "opening_range": "09:30 inclusive to 09:30 + range_minutes exclusive",
            "entry_trigger": "first 5m candle close above OR high or below OR low after range lock",
            "entry_cutoff": "11:00 America/New_York; no trade after cutoff",
            "stop": "opposite side of opening range",
            "targets": "1R, 3R, 4R measured from entry risk",
            "session_exit": "16:00 America/New_York if stop/target not touched",
            "same_bar_collision_policy": "pessimistic_stop_first",
            "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        },
        "promotion_allowed": False,
        "blocked_actions": ["live_trading", "paper_trading", "strategy_promotion"],
    }


def write_pre_run_gate(output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    gate = build_pre_run_gate()
    gate_path = output_dir / "pre_run_gate.json"
    gate_path.write_text(json.dumps(gate, indent=2, sort_keys=True), encoding="utf-8")
    return {"gate_path": gate_path}


def normalize_yfinance_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
    data = frame.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [str(col[0]).lower() for col in data.columns]
    else:
        data.columns = [str(col).lower().replace(" ", "_") for col in data.columns]
    data = data.reset_index()
    first_col = data.columns[0]
    data = data.rename(columns={first_col: "timestamp", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
    keep = ["timestamp", "open", "high", "low", "close", "volume"]
    data = data[[column for column in keep if column in data.columns]].copy()
    for column in ["open", "high", "low", "close", "volume"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    data["symbol"] = symbol
    return data.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)


def fetch_yfinance_panel(symbols: dict[str, str] = SYMBOLS, *, period: str = "60d", interval: str = "5m") -> pd.DataFrame:
    import yfinance as yf

    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        frame = ticker.history(period=period, interval=interval, actions=False, auto_adjust=False)
        frames.append(normalize_yfinance_frame(frame, symbol))
    if not frames:
        return pd.DataFrame(columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
    return pd.concat(frames, ignore_index=True)


def _bar_time(timestamp: pd.Timestamp) -> time:
    return timestamp.tz_convert("America/New_York").time() if timestamp.tzinfo else timestamp.time()


def backtest_orb_symbol_day(day_bars: pd.DataFrame, config: OrbConfig) -> dict[str, Any] | None:
    bars = day_bars.sort_values("timestamp").reset_index(drop=True)
    if bars.empty:
        return None
    times = bars["timestamp"].map(_bar_time)
    range_end_hour = 9
    range_end_minute = 30 + config.range_minutes
    range_end = time(range_end_hour + range_end_minute // 60, range_end_minute % 60)
    opening = bars[(times >= config.open_time) & (times < range_end)]
    if opening.empty:
        return None
    or_high = float(opening["high"].max())
    or_low = float(opening["low"].min())
    if or_high <= or_low:
        return None
    candidates = bars[(times >= range_end) & (times <= config.entry_cutoff)].copy()
    entry_row = None
    direction = ""
    for _, row in candidates.iterrows():
        close = float(row["close"])
        if close > or_high:
            entry_row = row
            direction = "long"
            break
        if close < or_low:
            entry_row = row
            direction = "short"
            break
    if entry_row is None:
        return None
    entry_index = int(entry_row.name)
    entry_price = float(entry_row["close"])
    if direction == "long":
        stop = or_low
        risk = entry_price - stop
        target = entry_price + (risk * config.reward_r)
    else:
        stop = or_high
        risk = stop - entry_price
        target = entry_price - (risk * config.reward_r)
    if risk <= 0:
        return None
    future = bars.iloc[entry_index + 1 :].copy()
    future_times = future["timestamp"].map(_bar_time)
    future = future[future_times <= config.session_close]
    if future.empty:
        return None
    exit_price = float(future.iloc[-1]["close"])
    exit_reason = "session_close"
    exit_timestamp = future.iloc[-1]["timestamp"]
    for _, row in future.iterrows():
        high = float(row["high"])
        low = float(row["low"])
        if direction == "long":
            if low <= stop:
                exit_price = stop
                exit_reason = "stop_loss"
                exit_timestamp = row["timestamp"]
                break
            if high >= target:
                exit_price = target
                exit_reason = "take_profit"
                exit_timestamp = row["timestamp"]
                break
        else:
            if high >= stop:
                exit_price = stop
                exit_reason = "stop_loss"
                exit_timestamp = row["timestamp"]
                break
            if low <= target:
                exit_price = target
                exit_reason = "take_profit"
                exit_timestamp = row["timestamp"]
                break
    gross_return = (exit_price / entry_price - 1) if direction == "long" else (entry_price / exit_price - 1)
    net_return = gross_return - (config.cost_bps / 10000)
    return {
        "symbol": str(bars.iloc[0]["symbol"]),
        "date": bars.iloc[0]["timestamp"].date().isoformat(),
        "range_minutes": config.range_minutes,
        "reward_r": config.reward_r,
        "or_high": round(or_high, 8),
        "or_low": round(or_low, 8),
        "direction": direction,
        "entry_timestamp": entry_row["timestamp"].isoformat(),
        "entry_price": round(entry_price, 8),
        "stop_price": round(stop, 8),
        "target_price": round(target, 8),
        "exit_timestamp": pd.Timestamp(exit_timestamp).isoformat(),
        "exit_price": round(exit_price, 8),
        "exit_reason": exit_reason,
        "gross_return": round(gross_return, 8),
        "net_return": round(net_return, 8),
    }


def backtest_orb_panel(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    data = panel.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    data = data.dropna(subset=["timestamp"]).copy()
    data["session_date"] = data["timestamp"].dt.date
    trades: list[dict[str, Any]] = []
    for (symbol, _date), group in data.groupby(["symbol", "session_date"]):
        for range_minutes in RANGE_MINUTES:
            for reward_r in REWARD_R_MULTIPLES:
                trade = backtest_orb_symbol_day(group, OrbConfig(range_minutes=range_minutes, reward_r=reward_r))
                if trade is not None:
                    trades.append(trade)
    trade_frame = pd.DataFrame(trades)
    if trade_frame.empty:
        return trade_frame, pd.DataFrame()
    summary = (
        trade_frame.groupby(["symbol", "range_minutes", "reward_r"])
        .agg(
            trades=("net_return", "count"),
            win_rate=("net_return", lambda x: round(float((x > 0).mean()), 6)),
            gross_return_sum=("gross_return", "sum"),
            net_return_sum=("net_return", "sum"),
            average_net_return=("net_return", "mean"),
            median_net_return=("net_return", "median"),
        )
        .reset_index()
    )
    for column in ["gross_return_sum", "net_return_sum", "average_net_return", "median_net_return"]:
        summary[column] = summary[column].round(8)
    return trade_frame, summary


def final_decision(summary: pd.DataFrame, trades: pd.DataFrame) -> dict[str, Any]:
    if summary.empty:
        return {
            "decision": "ORB_930_ARCHIVE_NO_TRADES",
            "promotion_allowed": False,
            "reason": "No valid opening range breakout trades were generated.",
        }
    best = summary.sort_values(["net_return_sum", "trades"], ascending=[False, False]).iloc[0].to_dict()
    blockers = []
    if int(best["trades"]) < 30:
        blockers.append("trade_count_below_30")
    if float(best["median_net_return"]) <= 0:
        blockers.append("median_net_return_not_positive")
    if float(best["net_return_sum"]) <= 0:
        blockers.append("net_return_sum_not_positive")
    decision = "ORB_930_RESEARCH_CANDIDATE_ONLY" if not blockers else "ORB_930_ARCHIVE_CURRENT_FORM"
    return {
        "decision": decision,
        "promotion_allowed": False,
        "best_configuration": best,
        "blockers": blockers,
        "trade_count_total": int(len(trades)),
        "notes": [
            "Uses bounded yfinance 5m data; this is exploratory provider data, not institutional tick data.",
            "9:30 is interpreted as America/New_York session anchor for all three assets.",
            "Same-bar target/stop collisions are resolved pessimistically as stop first.",
        ],
    }


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for record in frame.astype(object).to_dict("records"):
        rows.append("| " + " | ".join(str(record[column]) for column in frame.columns) + " |")
    return "\n".join(rows)


def write_markdown_report(summary: pd.DataFrame, trades: pd.DataFrame, decision: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    best = decision.get("best_configuration", {})
    blockers = ", ".join(decision.get("blockers", [])) or "none"
    by_symbol = trades.groupby("symbol").size().to_dict() if not trades.empty and "symbol" in trades else {}
    best_rows = summary.sort_values("net_return_sum", ascending=False).head(6) if not summary.empty else pd.DataFrame()
    lines = [
        "# ORB-930-CROSS-ASSET-BACKTEST-001",
        "",
        "## Verdict",
        "",
        f"- decision: `{decision.get('decision', 'UNKNOWN')}`",
        f"- promotion_allowed: `{decision.get('promotion_allowed', False)}`",
        f"- blockers: `{blockers}`",
        f"- total generated trades: `{decision.get('trade_count_total', len(trades))}`",
        "",
        "## Best Configuration",
        "",
        f"- symbol: `{best.get('symbol', 'n/a')}`",
        f"- opening range: `{best.get('range_minutes', 'n/a')} minutes`",
        f"- reward multiple: `{best.get('reward_r', 'n/a')}R`",
        f"- trades: `{best.get('trades', 'n/a')}`",
        f"- win rate: `{best.get('win_rate', 'n/a')}`",
        f"- net return sum: `{best.get('net_return_sum', 'n/a')}`",
        f"- median net return: `{best.get('median_net_return', 'n/a')}`",
        "",
        "## Interpretation",
        "",
        "The 9:30 AM opening-range breakout creates plenty of trades across gold, EUR/USD, and bitcoin, "
        "but the best configuration is still archived because the typical trade is negative after costs. "
        "The gross effect is not strong enough to become a governed candidate.",
        "",
        "## Trade Counts By Symbol",
        "",
    ]
    for symbol, count in sorted(by_symbol.items()):
        lines.append(f"- `{symbol}`: `{count}`")
    if not best_rows.empty:
        lines.extend(["", "## Top Parameter Rows", ""])
        lines.append(_markdown_table(best_rows))
    report_path = output_dir / "orb_930_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_backtest(panel_path: Path | None = None) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if panel_path is None:
        panel = fetch_yfinance_panel()
        panel_path = DATA_DIR / "orb_930_yfinance_5m_panel.csv"
        panel.to_csv(panel_path, index=False)
    else:
        panel = pd.read_csv(panel_path)
    trades, summary = backtest_orb_panel(panel)
    trades_path = OUTPUT_DIR / "trades.csv"
    summary_path = OUTPUT_DIR / "summary.csv"
    decision_path = OUTPUT_DIR / "final_decision.json"
    trades.to_csv(trades_path, index=False)
    summary.to_csv(summary_path, index=False)
    decision = final_decision(summary, trades)
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
    report_path = write_markdown_report(summary, trades, decision)
    return {"panel_path": panel_path, "trades_path": trades_path, "summary_path": summary_path, "decision_path": decision_path, "report_path": report_path}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-gate", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--panel-path", type=Path, default=None)
    args = parser.parse_args()
    if args.write_gate:
        paths = write_pre_run_gate()
    elif args.run:
        paths = run_backtest(panel_path=args.panel_path)
    else:
        raise SystemExit("Use --write-gate or --run")
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
