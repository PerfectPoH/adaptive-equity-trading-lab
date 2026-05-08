from __future__ import annotations

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
