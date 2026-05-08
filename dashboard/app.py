from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Adaptive Equity Trading Lab", layout="wide")
st.title("Adaptive Equity Trading Lab")
st.caption("Milestone 1 research dashboard. Results are prototype-only, not trading advice.")

RUNS_DIR = Path("experiments/runs")
LOG_PATH = Path("experiments/log.csv")
NEWS_ABLATION_PATH = Path("experiments/news_ablation_latest.csv")
THRESHOLD_VALIDATION_PATH = Path("experiments/threshold_validation_latest.csv")


def latest_run_dir() -> Path | None:
    runs = sorted([path for path in RUNS_DIR.glob("*") if path.is_dir()])
    return runs[-1] if runs else None


run_dir = latest_run_dir()

if LOG_PATH.exists():
    st.subheader("Experiment Log")
    log = pd.read_csv(LOG_PATH)
    st.dataframe(log.tail(20), use_container_width=True)
else:
    st.info("No experiment log yet. Run `python -m src.pipeline` first.")

if NEWS_ABLATION_PATH.exists() or THRESHOLD_VALIDATION_PATH.exists():
    st.subheader("Experiment Reports")
    if NEWS_ABLATION_PATH.exists():
        with st.expander("Latest News Ablation", expanded=False):
            st.dataframe(pd.read_csv(NEWS_ABLATION_PATH), use_container_width=True)
    if THRESHOLD_VALIDATION_PATH.exists():
        with st.expander("Latest Threshold Validation", expanded=True):
            threshold_report = pd.read_csv(THRESHOLD_VALIDATION_PATH)
            st.dataframe(threshold_report, use_container_width=True)

if run_dir is None:
    st.stop()

st.subheader(f"Latest Run: {run_dir.name}")

backtests_path = run_dir / "backtests.csv"
signals_path = run_dir / "signals.csv"
equity_path = run_dir / "equity_curves.csv"
analysis_path = run_dir / "analysis.csv"
analysis_summary_path = run_dir / "analysis_summary.json"
signal_diagnostics_path = run_dir / "signal_diagnostics.csv"
signal_diagnostics_summary_path = run_dir / "signal_diagnostics_summary.json"
threshold_diagnostics_path = run_dir / "threshold_diagnostics.csv"
threshold_diagnostics_summary_path = run_dir / "threshold_diagnostics_summary.json"
calibration_path = run_dir / "calibration.csv"
calibration_summary_path = run_dir / "calibration_summary.json"
trades_path = run_dir / "trades.csv"
trade_analysis_path = run_dir / "trade_analysis_by_symbol.csv"
trade_analysis_summary_path = run_dir / "trade_analysis_summary.json"

if analysis_summary_path.exists():
    summary = json.loads(analysis_summary_path.read_text(encoding="utf-8"))
    st.subheader("Run Analysis")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Signals", summary.get("total_signals", 0))
    c2.metric("Executable", summary.get("total_executable_signals", 0))
    c3.metric("Symbols w/ Trades", summary.get("symbols_with_trades", 0))
    c4.metric("Skipped", summary.get("total_skipped_signals", 0))
    c5.metric("Underperformers", summary.get("underperforming_symbols", 0))
    for finding in summary.get("primary_findings", []):
        st.write(f"- {finding}")

if backtests_path.exists():
    backtests = pd.read_csv(backtests_path)
    st.subheader("2024 Per-Symbol Backtests")
    st.dataframe(backtests, use_container_width=True)

    if {"symbol", "strategy_return", "buy_and_hold_return"}.issubset(backtests.columns):
        melted = backtests.melt(
            id_vars=["symbol"],
            value_vars=["strategy_return", "buy_and_hold_return"],
            var_name="series",
            value_name="return",
        )
        fig = px.bar(melted, x="symbol", y="return", color="series", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

if equity_path.exists():
    equity = pd.read_csv(equity_path, parse_dates=["Date"])
    if not equity.empty and {"Date", "symbol", "normalized_equity"}.issubset(equity.columns):
        st.subheader("Normalized Equity Curves")
        pivot = equity.pivot_table(index="Date", columns="symbol", values="normalized_equity")
        aggregate = pivot.mean(axis=1).rename("equal_weight_strategy")
        aggregate_frame = aggregate.reset_index()
        fig = px.line(aggregate_frame, x="Date", y="equal_weight_strategy")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Per-symbol equity curves"):
            long_equity = pivot.reset_index().melt(id_vars="Date", var_name="symbol", value_name="normalized_equity")
            fig = px.line(long_equity, x="Date", y="normalized_equity", color="symbol")
            st.plotly_chart(fig, use_container_width=True)

if analysis_path.exists():
    analysis = pd.read_csv(analysis_path)
    st.subheader("Per-Symbol Diagnosis")
    st.dataframe(analysis, use_container_width=True)

if signal_diagnostics_summary_path.exists():
    diagnostics_summary = json.loads(signal_diagnostics_summary_path.read_text(encoding="utf-8"))
    st.subheader("Signal Bottlenecks")
    d1, d2, d3 = st.columns(3)
    d1.metric("Scanner Pass Symbols", diagnostics_summary.get("symbols_with_scanner_pass", 0))
    d2.metric("Model Pass Symbols", diagnostics_summary.get("symbols_with_model_pass", 0))
    d3.metric("Signal Symbols", diagnostics_summary.get("symbols_with_signals", 0))
    bottlenecks = diagnostics_summary.get("primary_bottlenecks", {})
    if bottlenecks:
        st.write("Bottleneck counts:", bottlenecks)

if signal_diagnostics_path.exists():
    diagnostics = pd.read_csv(signal_diagnostics_path)
    st.dataframe(diagnostics, use_container_width=True)

if threshold_diagnostics_summary_path.exists():
    threshold_summary = json.loads(threshold_diagnostics_summary_path.read_text(encoding="utf-8"))
    st.subheader("Probability Threshold Diagnostics")
    st.metric("Recommended Threshold", threshold_summary.get("recommended_threshold"))
    st.caption(threshold_summary.get("reason", ""))

if threshold_diagnostics_path.exists():
    threshold_diagnostics = pd.read_csv(threshold_diagnostics_path)
    st.dataframe(threshold_diagnostics, use_container_width=True)

if calibration_summary_path.exists():
    calibration_summary = json.loads(calibration_summary_path.read_text(encoding="utf-8"))
    st.subheader("Model Calibration")
    cal_cols = st.columns(2)
    for idx, period in enumerate(["validation", "test"]):
        period_summary = calibration_summary.get(period, {})
        with cal_cols[idx]:
            st.metric(f"{period.title()} Brier", period_summary.get("brier_score"))
            st.metric(f"{period.title()} Mean Abs Error", period_summary.get("mean_abs_calibration_error"))

if calibration_path.exists():
    calibration = pd.read_csv(calibration_path)
    populated = calibration[calibration["count"] > 0]
    if not populated.empty:
        fig = px.line(
            populated,
            x="avg_predicted_probability",
            y="observed_success_rate",
            color="period",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("Calibration bins"):
        st.dataframe(calibration, use_container_width=True)

if trade_analysis_summary_path.exists():
    trade_summary = json.loads(trade_analysis_summary_path.read_text(encoding="utf-8"))
    st.subheader("Trade-Level Analysis")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Closed Trades", trade_summary.get("total_trades", 0))
    t2.metric("Trade Win Rate", trade_summary.get("win_rate"))
    t3.metric("Avg Trade Return", trade_summary.get("avg_return_pct"))
    t4.metric("Total PnL", trade_summary.get("total_pnl"))
    st.write("Worst trade:", trade_summary.get("worst_trade"))

if trade_analysis_path.exists():
    trade_analysis = pd.read_csv(trade_analysis_path)
    st.dataframe(trade_analysis, use_container_width=True)

if trades_path.exists():
    with st.expander("Closed trades"):
        trades = pd.read_csv(trades_path)
        st.dataframe(trades, use_container_width=True)

if signals_path.exists():
    signals = pd.read_csv(signals_path)
    st.subheader("Recent Signals")
    cols = [
        col
        for col in [
            "Date",
            "symbol",
            "Close",
            "scanner_score",
            "model_probability",
            "signal",
            "execution_valid",
            "execution_skip_reason",
        ]
        if col in signals.columns
    ]
    if cols:
        st.dataframe(signals[cols].tail(100), use_container_width=True)

st.subheader("Warnings & Limits")
st.warning(
    "This MVP uses yfinance data and simple next-open backtesting. It has survivorship bias, "
    "does not model live execution quality, and is not sufficient evidence for real capital allocation."
)
