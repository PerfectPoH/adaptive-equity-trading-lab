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

if run_dir is None:
    st.stop()

st.subheader(f"Latest Run: {run_dir.name}")

backtests_path = run_dir / "backtests.csv"
signals_path = run_dir / "signals.csv"
equity_path = run_dir / "equity_curves.csv"
analysis_path = run_dir / "analysis.csv"
analysis_summary_path = run_dir / "analysis_summary.json"

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
