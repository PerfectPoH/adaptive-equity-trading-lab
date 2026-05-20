from __future__ import annotations

import argparse
import hashlib
import json
import math
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.execution.market_impact import SquareRootImpactConfig, square_root_impact_bps


DEFAULT_DATA_DIR = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520")
DEFAULT_PREREG_DIR = Path("experiments/provider_aware_research/xmom_preregistered_research_plan_20260520")
DEFAULT_PRE_RUN_GATE_DIR = Path("experiments/provider_aware_research/xmom_pre_run_gate_20260520")
DEFAULT_OUTPUT_DIR = Path("experiments/runs/xmom_trial_001_20260520")
DEFAULT_TRIAL_ID = "TRIAL-XMOM-001"
DEFAULT_PREREG_ID = "PREREG-XMOM-001"


@dataclass(frozen=True)
class XMOMExecutionConfig:
    initial_cash: float = 100_000.0
    holding_window: int = 21
    minimum_price: float = 2.0
    minimum_dollar_volume: float = 1_000_000.0
    impact_coefficient_bps: float = 500.0
    max_position_dollar_volume_fraction: float = 0.20
    impact_participation_cap: float = 0.20
    rebalance_frequency: str = "monthly"
    top_bucket_selection: str = "top_decile"
    holdout_start: str = "2025-01-01"
    holdout_end: str = "2025-12-31"


def run_xmom_trial(
    *,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    prereg_dir: str | Path = DEFAULT_PREREG_DIR,
    pre_run_gate_dir: str | Path = DEFAULT_PRE_RUN_GATE_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    config: XMOMExecutionConfig = XMOMExecutionConfig(),
) -> dict[str, Any]:
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pre_run_report = _run_pre_run_gate(Path(pre_run_gate_dir))
    if pre_run_report.get("status") != "pass":
        raise RuntimeError(f"Pre-run gate did not pass: {pre_run_report.get('gate_decision')}")

    prices = pd.read_csv(data_path / "prices.csv")
    prices["date"] = pd.to_datetime(prices["date"])
    for column in ("open", "high", "low", "close", "volume"):
        prices[column] = pd.to_numeric(prices[column], errors="coerce")
    prices = prices.sort_values(["symbol", "date"]).reset_index(drop=True)

    universe = sorted(symbol for symbol in prices["symbol"].unique().tolist() if symbol != "IWM")
    trades, candidates = _generate_trades(prices, universe, config)
    benchmarks = _benchmark_report(prices, trades, config)
    summary = _portfolio_summary(trades, config.initial_cash)
    outlier = _outlier_breakdown(trades, config.initial_cash)
    equity_curve = _equity_curve(trades, config.initial_cash)

    config_payload = _config_payload(config, data_path, Path(prereg_dir), Path(pre_run_gate_dir))
    manifest = _run_manifest(config_payload, universe)
    manifest["trial_accounting"] = {
        "trial_id": DEFAULT_TRIAL_ID,
        "preregistration_id": DEFAULT_PREREG_ID,
        "trial_status": "executed_once",
        "execution_type": "preregistered_xmom_trial",
    }

    _write_outputs(output_path, manifest, trades, candidates, benchmarks, summary, outlier, equity_curve, pre_run_report)
    return {
        "output_dir": str(output_path),
        "run_id": manifest["run_id"],
        "total_trades": int(len(trades)),
        "return_pct": float(summary["return_pct"].iloc[0]),
        "primary_metric": float(benchmarks.loc[benchmarks["benchmark"].eq("iwm_holding_windows"), "excess_return"].iloc[0]),
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_xmom_trial(output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the single preregistered TRIAL-XMOM-001 execution.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser


def _run_pre_run_gate(gate_dir: Path) -> dict[str, Any]:
    from src.experiments.xmom_pre_run_gate_validator import validate_xmom_pre_run_gate

    return validate_xmom_pre_run_gate(gate_dir)


def _generate_trades(prices: pd.DataFrame, universe: list[str], config: XMOMExecutionConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    entries = _monthly_entry_dates(prices, config)
    price_by_symbol = {symbol: frame.reset_index(drop=True) for symbol, frame in prices.groupby("symbol")}
    trade_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    cash = config.initial_cash

    for entry_date in entries:
        signal_date = _previous_trading_date(prices, entry_date)
        if signal_date is None:
            continue
        scored = []
        for symbol in universe:
            frame = price_by_symbol[symbol]
            score = _score_symbol(frame, signal_date, config)
            if score is None:
                candidate_rows.append({"symbol": symbol, "signal_date": signal_date.date().isoformat(), "entry_date": entry_date.date().isoformat(), "candidate_status": "rejected", "reject_reason": "insufficient_history_or_liquidity"})
                continue
            candidate_rows.append({**score, "candidate_status": "accepted_for_ranking", "reject_reason": ""})
            scored.append(score)
        if not scored:
            continue
        scored = sorted(scored, key=lambda row: row["rank_aggregate_score"], reverse=True)
        selection_count = max(1, math.ceil(len(scored) * 0.10))
        for selected in scored[:selection_count]:
            trade = _plan_trade(price_by_symbol[selected["symbol"]], selected, entry_date, cash, config)
            if trade is None:
                continue
            trade_rows.append(trade)
            cash += float(trade["pnl"])

    return pd.DataFrame(trade_rows), pd.DataFrame(candidate_rows)


def _score_symbol(frame: pd.DataFrame, signal_date: pd.Timestamp, config: XMOMExecutionConfig) -> dict[str, Any] | None:
    signal_rows = frame[frame["date"].le(signal_date)]
    if len(signal_rows) < 253:
        return None
    signal = signal_rows.iloc[-1]
    if float(signal["close"]) < config.minimum_price:
        return None
    dollar_volume = (signal_rows["close"] * signal_rows["volume"]).tail(20).mean()
    if not math.isfinite(float(dollar_volume)) or float(dollar_volume) < config.minimum_dollar_volume:
        return None
    returns = {}
    for name, lookback in {"momentum_3m": 63, "momentum_6m": 126, "momentum_12m": 252}.items():
        base = signal_rows.iloc[-lookback - 1]
        returns[name] = float(signal["close"] / base["close"] - 1)
    rank_aggregate_score = sum(returns.values()) / len(returns)
    volatility = float(signal_rows["close"].pct_change().tail(20).std())
    return {
        "symbol": str(signal["symbol"]),
        "signal_date": signal_date.date().isoformat(),
        **returns,
        "rank_aggregate_score": rank_aggregate_score,
        "signal_close": float(signal["close"]),
        "avg_dollar_volume_20d": float(dollar_volume),
        "rolling_volatility_20d": 0.0 if not math.isfinite(volatility) else volatility,
    }


def _plan_trade(frame: pd.DataFrame, signal: dict[str, Any], entry_date: pd.Timestamp, cash: float, config: XMOMExecutionConfig) -> dict[str, Any] | None:
    entry_matches = frame[frame["date"].eq(entry_date)]
    if entry_matches.empty:
        return None
    entry_idx = int(entry_matches.index[0])
    exit_idx = entry_idx + config.holding_window
    if exit_idx >= len(frame):
        return None
    entry_row = frame.loc[entry_idx]
    exit_row = frame.loc[exit_idx]
    entry_reference_price = float(entry_row["open"])
    exit_price = float(exit_row["close"])
    adv_notional = float(signal["avg_dollar_volume_20d"])
    max_liquidity_notional = adv_notional * config.max_position_dollar_volume_fraction
    target_notional = min(cash, max_liquidity_notional)
    impact_bps = square_root_impact_bps(
        order_notional=target_notional,
        adv_notional=adv_notional,
        volatility=max(float(signal["rolling_volatility_20d"]), 0.0),
        config=SquareRootImpactConfig(config.impact_coefficient_bps, config.impact_participation_cap),
    )
    if math.isinf(impact_bps):
        return None
    impact_cost_pct = impact_bps / 10_000.0
    entry_price = entry_reference_price * (1 + impact_cost_pct)
    position_size = math.floor(target_notional / entry_price)
    if position_size <= 0:
        return None
    position_notional = position_size * entry_price
    pnl = position_size * (exit_price - entry_price)
    return_pct = pnl / position_notional if position_notional else 0.0
    return {
        "symbol": signal["symbol"],
        "signal_date": signal["signal_date"],
        "entry_date": entry_date.date().isoformat(),
        "exit_date": pd.Timestamp(exit_row["date"]).date().isoformat(),
        "entry_reference_price": entry_reference_price,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "position_size": int(position_size),
        "position_notional": float(position_notional),
        "max_liquidity_notional": float(max_liquidity_notional),
        "estimated_cost_pct": float(impact_cost_pct),
        "impact_cost_pct": float(impact_cost_pct),
        "participation_rate": float(position_notional / adv_notional),
        "impact_bps": float(impact_bps),
        "momentum_3m": signal["momentum_3m"],
        "momentum_6m": signal["momentum_6m"],
        "momentum_12m": signal["momentum_12m"],
        "rank_aggregate_score": signal["rank_aggregate_score"],
        "avg_dollar_volume_20d": signal["avg_dollar_volume_20d"],
        "rolling_volatility_20d": signal["rolling_volatility_20d"],
        "pnl": float(pnl),
        "return_pct": float(return_pct),
        "cash_after_entry": float(cash - position_notional),
        "cash_after_exit": float(cash + pnl),
    }


def _monthly_entry_dates(prices: pd.DataFrame, config: XMOMExecutionConfig) -> list[pd.Timestamp]:
    all_dates = sorted(pd.to_datetime(prices["date"].unique()))
    start = pd.Timestamp(config.holdout_start)
    end = pd.Timestamp(config.holdout_end)
    holdout_dates = [date for date in all_dates if start <= date <= end]
    entries: list[pd.Timestamp] = []
    seen: set[tuple[int, int]] = set()
    for date in holdout_dates:
        key = (date.year, date.month)
        if key not in seen:
            entries.append(date)
            seen.add(key)
    return entries


def _previous_trading_date(prices: pd.DataFrame, entry_date: pd.Timestamp) -> pd.Timestamp | None:
    dates = sorted(pd.to_datetime(prices["date"].unique()))
    previous = [date for date in dates if date < entry_date]
    return previous[-1] if previous else None


def _benchmark_report(prices: pd.DataFrame, trades: pd.DataFrame, config: XMOMExecutionConfig) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["benchmark", "return", "excess_return", "observations", "description"])
    iwm = prices[prices["symbol"].eq("IWM")].reset_index(drop=True)
    returns = []
    for _, trade in trades.iterrows():
        entry_date = pd.Timestamp(trade["entry_date"])
        exit_date = pd.Timestamp(trade["exit_date"])
        entry = iwm[iwm["date"].eq(entry_date)]
        exit_ = iwm[iwm["date"].eq(exit_date)]
        if entry.empty or exit_.empty:
            continue
        returns.append(float(exit_.iloc[0]["close"] / entry.iloc[0]["open"] - 1))
    iwm_return = float(sum(returns) / len(returns)) if returns else 0.0
    trade_return = float(trades["pnl"].sum() / config.initial_cash)
    return pd.DataFrame(
        [
            {
                "benchmark": "iwm_holding_windows",
                "return": iwm_return,
                "excess_return": trade_return - iwm_return,
                "observations": len(returns),
                "description": "Average IWM open-to-close return over matching XMOM holding windows.",
            },
            {
                "benchmark": "cash_flat",
                "return": 0.0,
                "excess_return": trade_return,
                "observations": len(trades),
                "description": "Cash baseline.",
            },
        ]
    )


def _portfolio_summary(trades: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    total_pnl = float(trades["pnl"].sum()) if not trades.empty else 0.0
    return pd.DataFrame(
        [
            {
                "initial_cash": initial_cash,
                "ending_cash": initial_cash + total_pnl,
                "total_pnl": total_pnl,
                "return_pct": total_pnl / initial_cash,
                "total_trades": int(len(trades)),
                "total_rejections": 0,
            }
        ]
    )


def _outlier_breakdown(trades: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame([{"outlier_concentration_alert": False, "sign_flip_excluding_top_3": False, "pnl_excluding_top_3": 0.0}])
    pnl = trades["pnl"].astype(float)
    total = float(pnl.sum())
    top = pnl.sort_values(ascending=False)
    ex_top3 = float(total - top.head(3).sum())
    return pd.DataFrame(
        [
            {
                "total_trades": int(len(trades)),
                "total_pnl": total,
                "gross_profit": float(pnl[pnl > 0].sum()),
                "gross_loss": float(pnl[pnl < 0].sum()),
                "top_1_pnl_contribution_pct": float(top.head(1).sum() / total) if total else 0.0,
                "top_3_pnl_contribution_pct": float(top.head(3).sum() / total) if total else 0.0,
                "outlier_concentration_alert": bool(abs(top.head(3).sum()) > abs(total) and total > 0),
                "pnl_excluding_top_3": ex_top3,
                "sign_flip_excluding_top_3": bool(total != 0 and ex_top3 * total < 0),
                "portfolio_return_excluding_top_3": ex_top3 / initial_cash,
            }
        ]
    )


def _equity_curve(trades: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    rows = [{"date": "", "equity": initial_cash, "event": "initial"}]
    equity = initial_cash
    for _, trade in trades.iterrows():
        equity += float(trade["pnl"])
        rows.append({"date": trade["exit_date"], "equity": equity, "event": f"exit_{trade['symbol']}"})
    return pd.DataFrame(rows)


def _config_payload(config: XMOMExecutionConfig, data_path: Path, prereg_dir: Path, pre_run_gate_dir: Path) -> dict[str, Any]:
    return {
        "strategy": "xmom_preregistered_v1",
        "data_dir": str(data_path).replace("\\", "/"),
        "preregistration_dir": str(prereg_dir).replace("\\", "/"),
        "pre_run_gate_dir": str(pre_run_gate_dir).replace("\\", "/"),
        "execution": asdict(config),
        "portfolio": {"execution": {
            "impact_coefficient_bps": config.impact_coefficient_bps,
            "impact_participation_cap": config.impact_participation_cap,
            "max_position_dollar_volume_fraction": config.max_position_dollar_volume_fraction,
        }},
    }


def _run_manifest(config_payload: dict[str, Any], universe: list[str]) -> dict[str, Any]:
    created_at = datetime.now(UTC).isoformat()
    canonical = json.dumps(config_payload, sort_keys=True, separators=(",", ":"))
    return {
        "run_id": f"xmom_trial_001_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "schema_version": "1",
        "created_at": created_at,
        "git_commit": _git_commit(),
        "host": socket.gethostname(),
        "config_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "universe": universe,
        "extras": {"purpose": "TRIAL-XMOM-001"},
        "config": config_payload,
        "trial_accounting": {},
    }


def _write_outputs(
    output_path: Path,
    manifest: dict[str, Any],
    trades: pd.DataFrame,
    candidates: pd.DataFrame,
    benchmarks: pd.DataFrame,
    summary: pd.DataFrame,
    outlier: pd.DataFrame,
    equity_curve: pd.DataFrame,
    pre_run_report: dict[str, Any],
) -> None:
    (output_path / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_path / "pre_run_gate_report.json").write_text(json.dumps(pre_run_report, indent=2, sort_keys=True), encoding="utf-8")
    candidates.to_csv(output_path / "candidate_export.csv", index=False)
    benchmarks.to_csv(output_path / "benchmark_report.csv", index=False)
    trades.to_csv(output_path / "portfolio_trade_log.csv", index=False)
    equity_curve.to_csv(output_path / "portfolio_equity_curve.csv", index=False)
    pd.DataFrame(columns=["symbol", "signal_date", "reject_reason"]).to_csv(output_path / "portfolio_rejections.csv", index=False)
    summary.to_csv(output_path / "portfolio_summary.csv", index=False)
    outlier.to_csv(output_path / "portfolio_outlier_breakdown.csv", index=False)
    report = _markdown_report(manifest, summary, benchmarks, outlier)
    (output_path / "small_cap_backtest_report.md").write_text(report, encoding="utf-8")


def _markdown_report(manifest: dict[str, Any], summary: pd.DataFrame, benchmarks: pd.DataFrame, outlier: pd.DataFrame) -> str:
    summary_row = summary.iloc[0].to_dict()
    primary = benchmarks[benchmarks["benchmark"].eq("iwm_holding_windows")].iloc[0].to_dict()
    outlier_row = outlier.iloc[0].to_dict()
    primary_passed = float(primary["excess_return"]) > 0
    if primary_passed and outlier.sign_flip_excluding_top_3:
        decision = "primary_go_rule_passed_but_outlier_stress_blocks_promotion"
    elif primary_passed:
        decision = "go_rule_passed"
    else:
        decision = "go_rule_failed"
    return "\n".join(
        [
            "# TRIAL-XMOM-001 Report",
            "",
            f"run_id: `{manifest['run_id']}`",
            f"config_hash: `{manifest['config_hash']}`",
            "",
            "## Summary",
            "",
            f"- total_trades: {summary_row['total_trades']}",
            f"- total_pnl: {summary_row['total_pnl']}",
            f"- return_pct: {summary_row['return_pct']}",
            f"- iwm_holding_window_return: {primary['return']}",
            f"- excess_return_vs_iwm_net_of_costs: {primary['excess_return']}",
            f"- preregistered_decision: `{decision}`",
            "",
            "## Outlier Diagnostics",
            "",
            f"- outlier_concentration_alert: {outlier_row.get('outlier_concentration_alert')}",
            f"- sign_flip_excluding_top_3: {outlier_row.get('sign_flip_excluding_top_3')}",
            f"- pnl_excluding_top_3: {outlier_row.get('pnl_excluding_top_3')}",
            "",
            "No paper/live trading or strategy promotion is authorized by this report.",
            "",
        ]
    )


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
