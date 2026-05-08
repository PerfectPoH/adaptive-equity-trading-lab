from __future__ import annotations

import math
from typing import Any

import pandas as pd


def build_run_analysis(
    signals: pd.DataFrame,
    backtests: pd.DataFrame,
    start: str = "2024-01-01",
    end: str = "2024-12-31",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    dates = pd.to_datetime(signals.index)
    date_mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    test_signals = signals.loc[date_mask].copy()
    per_symbol_rows: list[dict[str, Any]] = []

    symbols = sorted(set(test_signals.get("symbol", pd.Series(dtype=str)).dropna().astype(str)))
    backtest_by_symbol = _rows_by_symbol(backtests)

    for symbol in symbols:
        symbol_signals = test_signals[test_signals["symbol"] == symbol]
        signal_mask = symbol_signals.get("signal", False).astype(bool)
        valid_mask = signal_mask & symbol_signals.get("execution_valid", False).astype(bool)
        skipped_mask = signal_mask & ~symbol_signals.get("execution_valid", False).astype(bool)

        backtest_row = backtest_by_symbol.get(symbol, {})
        row = {
            "symbol": symbol,
            "bars": int(len(symbol_signals)),
            "signals": int(signal_mask.sum()),
            "executable_signals": int(valid_mask.sum()),
            "skipped_signals": int(skipped_mask.sum()),
            "top_skip_reason": _top_skip_reason(symbol_signals.loc[skipped_mask]),
            "avg_probability_on_signals": _mean_on_mask(symbol_signals, "model_probability", signal_mask),
            "avg_scanner_score_on_signals": _mean_on_mask(symbol_signals, "scanner_score", signal_mask),
            "trades": _safe_number(backtest_row.get("trades")),
            "strategy_return": _safe_number(backtest_row.get("strategy_return")),
            "buy_and_hold_return": _safe_number(backtest_row.get("buy_and_hold_return")),
            "excess_return": _safe_number(backtest_row.get("excess_return")),
            "max_drawdown": _safe_number(backtest_row.get("max_drawdown")),
            "win_rate": _safe_number(backtest_row.get("win_rate")),
        }
        row["diagnosis"] = _diagnose(row)
        per_symbol_rows.append(row)

    analysis = pd.DataFrame(per_symbol_rows)
    summary = summarize_analysis(analysis)
    return analysis, summary


def build_signal_diagnostics(
    signals: pd.DataFrame,
    start: str = "2024-01-01",
    end: str = "2024-12-31",
    min_scanner_score: float = 70,
    min_model_probability: float = 0.60,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    dates = pd.to_datetime(signals.index)
    date_mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    test_signals = signals.loc[date_mask].copy()
    rows: list[dict[str, Any]] = []

    symbols = sorted(set(test_signals.get("symbol", pd.Series(dtype=str)).dropna().astype(str)))
    for symbol in symbols:
        symbol_rows = test_signals[test_signals["symbol"] == symbol]
        scanner_score = pd.to_numeric(symbol_rows.get("scanner_score"), errors="coerce")
        probability = pd.to_numeric(symbol_rows.get("model_probability"), errors="coerce")
        scanner_pass = scanner_score > min_scanner_score
        model_pass = probability > min_model_probability
        market_pass = symbol_rows.get("spy_trend_positive", False).fillna(False).astype(bool)
        signal = symbol_rows.get("signal", False).fillna(False).astype(bool)

        row = {
            "symbol": symbol,
            "bars": int(len(symbol_rows)),
            "scanner_pass_days": int(scanner_pass.sum()),
            "model_pass_days": int(model_pass.sum()),
            "market_pass_days": int(market_pass.sum()),
            "scanner_and_model_days": int((scanner_pass & model_pass).sum()),
            "signal_days": int(signal.sum()),
            "scanner_score_mean": _safe_number(scanner_score.mean()),
            "scanner_score_p90": _safe_number(scanner_score.quantile(0.90)),
            "scanner_score_max": _safe_number(scanner_score.max()),
            "model_probability_mean": _safe_number(probability.mean()),
            "model_probability_p90": _safe_number(probability.quantile(0.90)),
            "model_probability_max": _safe_number(probability.max()),
        }
        row["bottleneck"] = _diagnose_signal_bottleneck(row)
        rows.append(row)

    diagnostics = pd.DataFrame(rows)
    return diagnostics, summarize_signal_diagnostics(diagnostics)


def summarize_signal_diagnostics(diagnostics: pd.DataFrame) -> dict[str, Any]:
    if diagnostics.empty:
        return {
            "symbols_analyzed": 0,
            "symbols_with_scanner_pass": 0,
            "symbols_with_model_pass": 0,
            "symbols_with_signals": 0,
            "primary_bottlenecks": [],
        }

    bottlenecks = diagnostics["bottleneck"].astype(str).value_counts().to_dict()
    return {
        "symbols_analyzed": int(len(diagnostics)),
        "symbols_with_scanner_pass": int((diagnostics["scanner_pass_days"] > 0).sum()),
        "symbols_with_model_pass": int((diagnostics["model_pass_days"] > 0).sum()),
        "symbols_with_signals": int((diagnostics["signal_days"] > 0).sum()),
        "total_scanner_pass_days": int(diagnostics["scanner_pass_days"].sum()),
        "total_model_pass_days": int(diagnostics["model_pass_days"].sum()),
        "total_signal_days": int(diagnostics["signal_days"].sum()),
        "primary_bottlenecks": bottlenecks,
    }


def summarize_analysis(analysis: pd.DataFrame) -> dict[str, Any]:
    if analysis.empty:
        return {
            "symbols_analyzed": 0,
            "total_signals": 0,
            "total_executable_signals": 0,
            "total_skipped_signals": 0,
            "underperforming_symbols": 0,
            "outperforming_symbols": 0,
            "primary_findings": ["No analysis rows were generated."],
        }

    total_signals = int(analysis["signals"].sum())
    total_executable = int(analysis["executable_signals"].sum())
    total_skipped = int(analysis["skipped_signals"].sum())
    symbols_with_signals = int((analysis["signals"] > 0).sum())
    symbols_with_trades = int((analysis["trades"] > 0).sum())
    underperforming = int((analysis["excess_return"] < 0).sum())
    outperforming = int((analysis["excess_return"] > 0).sum())
    top_skip_reason = _series_mode(analysis["top_skip_reason"].replace("", pd.NA).dropna())

    findings: list[str] = []
    if underperforming:
        findings.append(f"{underperforming} symbols underperformed buy-and-hold in the 2024 test window.")
    if total_signals == 0:
        findings.append("The scanner/model stack generated no test-window signals.")
    else:
        if symbols_with_signals < len(analysis):
            findings.append(f"Signals were concentrated in {symbols_with_signals} of {len(analysis)} symbols.")
        if symbols_with_trades < symbols_with_signals:
            findings.append(f"Only {symbols_with_trades} symbols produced closed trades.")
        if total_executable < total_signals:
            findings.append(f"{total_skipped} of {total_signals} signals were skipped by execution rules.")
    if top_skip_reason:
        findings.append(f"Most common execution skip reason: {top_skip_reason}.")
    if not findings:
        findings.append("No obvious structural issue found in the first-pass analysis.")

    return {
        "symbols_analyzed": int(len(analysis)),
        "total_signals": total_signals,
        "total_executable_signals": total_executable,
        "total_skipped_signals": total_skipped,
        "symbols_with_signals": symbols_with_signals,
        "symbols_with_trades": symbols_with_trades,
        "underperforming_symbols": underperforming,
        "outperforming_symbols": outperforming,
        "top_skip_reason": top_skip_reason,
        "mean_strategy_return": _safe_number(analysis["strategy_return"].mean()),
        "mean_buy_and_hold_return": _safe_number(analysis["buy_and_hold_return"].mean()),
        "mean_excess_return": _safe_number(analysis["excess_return"].mean()),
        "primary_findings": findings,
    }


def _rows_by_symbol(backtests: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if backtests.empty or "symbol" not in backtests.columns:
        return {}
    return {
        str(row["symbol"]): row.to_dict()
        for _, row in backtests.iterrows()
        if pd.notna(row.get("symbol"))
    }


def _top_skip_reason(rows: pd.DataFrame) -> str:
    if rows.empty or "execution_skip_reason" not in rows.columns:
        return ""
    return _series_mode(rows["execution_skip_reason"].replace("", pd.NA).dropna())


def _series_mode(series: pd.Series) -> str:
    if series.empty:
        return ""
    counts = series.astype(str).value_counts()
    return str(counts.index[0]) if not counts.empty else ""


def _mean_on_mask(frame: pd.DataFrame, column: str, mask: pd.Series) -> float:
    if column not in frame.columns or not bool(mask.any()):
        return float("nan")
    return _safe_number(frame.loc[mask, column].mean())


def _safe_number(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed if math.isfinite(parsed) else float("nan")


def _diagnose(row: dict[str, Any]) -> str:
    if row["signals"] == 0:
        return "no_signals"
    if row["executable_signals"] == 0:
        return "signals_not_executable"
    if row["trades"] == 0:
        return "no_closed_trades"
    if row["excess_return"] > 0:
        return "outperformed_benchmark"
    if row["strategy_return"] < 0:
        return "negative_strategy_return"
    if row["buy_and_hold_return"] > 0 and row["excess_return"] < 0:
        return "underexposed_to_strong_uptrend"
    return "flat_or_inconclusive"


def _diagnose_signal_bottleneck(row: dict[str, Any]) -> str:
    if row["scanner_pass_days"] == 0:
        return "scanner_filter"
    if row["model_pass_days"] == 0:
        return "model_probability_filter"
    if row["market_pass_days"] == 0:
        return "market_trend_filter"
    if row["scanner_and_model_days"] == 0:
        return "scanner_model_misalignment"
    if row["signal_days"] == 0:
        return "combined_filter"
    return "passes_signal_stack"
