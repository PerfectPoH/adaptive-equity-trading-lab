from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any

import pandas as pd

from src.experiments.lowvol_tradability_preregistration_validator import validate_lowvol_tradability_preregistration


RUN_ID = "LOWVOL-TRADABILITY-BACKTEST-001"
TRIAL_ID = "TRIAL-LOWVOL-TRADABILITY-001"
SPEC_DIR = Path("experiments/provider_aware_research/lowvol_tradability_preregistration_20260523")
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/LOWVOL-TRADABILITY-BACKTEST-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-LowVol-Tradability-Trial-001-2026-05-23.md")


def run_lowvol_tradability_trial_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    price_file: str | Path = PRICE_FILE,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    minimum_trade_count: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prereg = validate_lowvol_tradability_preregistration(spec_dir)
    _write_json(output / "preflight_report.json", prereg)
    if prereg["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = json.loads((Path(spec_dir) / "preregistration_manifest.json").read_text(encoding="utf-8"))
    prices = pd.read_csv(price_file)
    trades = build_lowvol_tradability_trades(
        prices,
        start_date=str(manifest["start_date"]),
        end_date=str(manifest["end_date"]),
        lookback_days=int(manifest["lookback_days"]),
        holding_days=int(manifest["holding_days"]),
        rebalance_step_days=int(manifest["rebalance_step_days"]),
        min_median_dollar_volume=float(manifest["min_median_dollar_volume"]),
        min_price=float(manifest["min_price"]),
        round_trip_cost_bps=int(manifest["round_trip_cost_bps"]),
        allowed_symbols=set(manifest["allowed_symbols"]),
    )
    summary = summarize_lowvol_backtest(trades, minimum_trade_count=minimum_trade_count or int(manifest["minimum_trade_count"]))
    decision = _final_decision(summary)
    _write_csv(output / "trade_log.csv", list(trades[0].keys()) if trades else [], trades)
    _write_json(output / "backtest_summary.json", summary)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), summary, decision)
    return decision


def build_lowvol_tradability_trades(
    prices: pd.DataFrame,
    *,
    start_date: str,
    end_date: str,
    lookback_days: int,
    holding_days: int,
    rebalance_step_days: int,
    min_median_dollar_volume: float,
    min_price: float,
    round_trip_cost_bps: int,
    allowed_symbols: set[str] | None = None,
) -> list[dict[str, Any]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if allowed_symbols is not None:
        frame = frame[frame["symbol"].astype(str).isin(allowed_symbols)].copy()
    frame = frame.sort_values(["date", "symbol"]).reset_index(drop=True)
    trading_dates = sorted(frame["date"].drop_duplicates().tolist())
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    candidate_signal_dates = [date for date in trading_dates if start <= date <= end]
    trades: list[dict[str, Any]] = []
    cost = round_trip_cost_bps / 10_000.0
    for signal_date in candidate_signal_dates[::rebalance_step_days]:
        ranked = _rank_candidates(frame, signal_date, lookback_days, min_median_dollar_volume, min_price)
        if not ranked:
            continue
        entry_date = _next_trading_date(trading_dates, signal_date)
        if entry_date is None:
            continue
        exit_date = _offset_trading_date(trading_dates, entry_date, holding_days)
        if exit_date is None or exit_date > end:
            continue
        selected = ranked[0]
        entry = _row(frame, selected["symbol"], entry_date)
        exit_ = _row(frame, selected["symbol"], exit_date)
        if entry is None or exit_ is None:
            continue
        entry_open = float(entry["open"])
        exit_close = float(exit_["close"])
        if entry_open <= 0:
            continue
        gross = exit_close / entry_open - 1.0
        trades.append(
            {
                "run_id": RUN_ID,
                "trial_id": TRIAL_ID,
                "signal_date": signal_date.date().isoformat(),
                "entry_date": entry_date.date().isoformat(),
                "exit_date": exit_date.date().isoformat(),
                "selected_symbol": selected["symbol"],
                "realized_volatility_60d": round(float(selected["volatility"]), 10),
                "median_dollar_volume_60d": round(float(selected["median_dollar_volume"]), 4),
                "signal_close": round(float(selected["signal_close"]), 6),
                "entry_open": round(entry_open, 6),
                "exit_close": round(exit_close, 6),
                "gross_return": round(gross, 10),
                "round_trip_cost_bps": round_trip_cost_bps,
                "net_return": round(gross - cost, 10),
                "provider_query_performed": False,
                "market_data_downloaded": False,
                "parameter_sweep_performed": False,
                "paper_trading_performed": False,
                "live_trading_performed": False,
                "promotion_allowed": False,
            }
        )
    return trades


def summarize_lowvol_backtest(trades: list[dict[str, Any]], *, minimum_trade_count: int) -> dict[str, Any]:
    gross = [float(row["gross_return"]) for row in trades]
    net = [float(row["net_return"]) for row in trades]
    total_gross = sum(gross)
    total_net = sum(net)
    win_rate = sum(1 for value in net if value > 0) / len(net) if net else 0.0
    median_net = median(net) if net else 0.0
    ex_top3 = _sum_excluding_top(net, 3)
    blockers: list[str] = []
    if len(trades) < minimum_trade_count:
        blockers.append(f"trade_count_below_{minimum_trade_count}")
    if total_net <= 0:
        blockers.append("net_return_not_positive_after_500bps")
    if median_net <= 0:
        blockers.append("median_net_return_not_positive")
    if total_net > 0 and ex_top3 <= 0:
        blockers.append("sign_flip_ex_top3")
    decision = "LOWVOL_TRADABILITY_CANDIDATE_ONLY_REQUIRES_SEPARATE_VALIDATION" if not blockers else "LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM"
    return {
        "status": "backtest_complete_existing_daily_artifacts_only",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "trade_count": len(trades),
        "minimum_trade_count": minimum_trade_count,
        "gross_return_sum": round(total_gross, 10),
        "net_return_sum_after_500bps": round(total_net, 10),
        "median_net_return": round(median_net, 10),
        "net_win_rate": round(win_rate, 6),
        "net_return_sum_ex_top3": round(ex_top3, 10),
        "symbols_traded": sorted({str(row["selected_symbol"]) for row in trades}),
        "candidate_allowed": not blockers,
        "promotion_allowed": False,
        "blockers": blockers or ["candidate_requires_separate_validation_gate"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": True,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def validate_lowvol_tradability_trial_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "trade_log.csv", "backtest_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    trades = _read_csv(path / "trade_log.csv")
    summary = json.loads((path / "backtest_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(trades[0].keys()) if trades else set()
    required_cols = {"signal_date", "entry_date", "exit_date", "selected_symbol", "gross_return", "net_return"}
    forbidden_cols = {"optimized_threshold", "sweep_id", "short_return"}
    _check(checks, "trade_log_non_empty", len(trades) > 0, f"rows={len(trades)}")
    _check(checks, "required_columns_present", required_cols.issubset(columns), f"missing={sorted(required_cols - columns)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "summary_existing_data_only", summary.get("provider_query_performed") is False and summary.get("market_data_downloaded") is False, str(summary))
    _check(checks, "summary_backtest_true", summary.get("backtest_performed") is True, str(summary.get("backtest_performed")))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _validation_report(checks)


def _rank_candidates(
    prices: pd.DataFrame,
    signal_date: pd.Timestamp,
    lookback_days: int,
    min_median_dollar_volume: float,
    min_price: float,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for symbol, symbol_prices in prices.groupby("symbol"):
        history = symbol_prices[symbol_prices["date"] <= signal_date].sort_values("date").tail(lookback_days + 1)
        if len(history) < lookback_days + 1:
            continue
        returns = history["close"].astype(float).pct_change().dropna()
        if len(returns) < lookback_days:
            continue
        dollar_volume = history.tail(lookback_days)["close"].astype(float) * history.tail(lookback_days)["volume"].astype(float)
        signal_close = float(history.iloc[-1]["close"])
        median_dollar_volume = float(dollar_volume.median())
        if signal_close < min_price or median_dollar_volume < min_median_dollar_volume:
            continue
        volatility = float(returns.std(ddof=0))
        if not math.isfinite(volatility):
            continue
        ranked.append(
            {
                "symbol": str(symbol),
                "volatility": volatility,
                "median_dollar_volume": median_dollar_volume,
                "signal_close": signal_close,
            }
        )
    return sorted(ranked, key=lambda row: (row["volatility"], -row["median_dollar_volume"], row["symbol"]))


def _row(frame: pd.DataFrame, symbol: str, date: pd.Timestamp) -> pd.Series | None:
    rows = frame[frame["symbol"].astype(str).eq(symbol) & frame["date"].eq(date)]
    if rows.empty:
        return None
    return rows.iloc[0]


def _next_trading_date(trading_dates: list[pd.Timestamp], signal_date: pd.Timestamp) -> pd.Timestamp | None:
    for date in trading_dates:
        if date > signal_date:
            return date
    return None


def _offset_trading_date(trading_dates: list[pd.Timestamp], entry_date: pd.Timestamp, offset: int) -> pd.Timestamp | None:
    try:
        index = trading_dates.index(entry_date)
    except ValueError:
        return None
    target = index + offset
    return trading_dates[target] if target < len(trading_dates) else None


def _sum_excluding_top(values: list[float], count: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values, reverse=True)
    return sum(ordered[count:]) if len(ordered) > count else 0.0


def _final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "trade_count": summary["trade_count"],
        "gross_return_sum": summary["gross_return_sum"],
        "net_return_sum_after_500bps": summary["net_return_sum_after_500bps"],
        "candidate_allowed": summary["candidate_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": True,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "LOWVOL_TRADABILITY_BACKTEST_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, summary: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report LowVol Tradability Trial 001 - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Existing Databento daily OHLCV artifact only. No provider query, market-data download, intraday query, parameter sweep, short selling, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Trade count: {summary['trade_count']}\n"
        f"- Gross return sum: {summary['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {summary['net_return_sum_after_500bps']}\n"
        f"- Median net return: {summary['median_net_return']}\n"
        f"- Net win rate: {summary['net_win_rate']}\n"
        f"- Net return sum ex-top3: {summary['net_return_sum_ex_top3']}\n"
        f"- Symbols traded: {', '.join(summary['symbols_traded'])}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Interpretation\n\n"
        "This is a long-only low-volatility/tradability backtest, not a fundamental-quality strategy. It can only become a candidate if it survives the 500 bps cost model, sample-size gate, median-return gate and outlier-resistance gate.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "LOWVOL_TRADABILITY_BACKTEST_OUTPUT_PASS" if failed == 0 else "LOWVOL_TRADABILITY_BACKTEST_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LowVol Tradability Trial 001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_lowvol_tradability_trial_001()
    report = validate_lowvol_tradability_trial_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
