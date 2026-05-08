# Adaptive Equity Trading Lab

Personal quantitative-trading research lab for US equities.

The Milestone 1 goal is not to build a profitable bot. The goal is to build a reproducible research pipeline that downloads historical daily data, creates point-in-time features, trains a simple ML model, generates signals, backtests them with next-open execution, logs experiments, and shows results in a Streamlit dashboard.

## Guiding Principle

```text
Prototype != reliable strategy
Backtest != real trading
Paper trading != live trading
Live small != scaling
```

## Milestone 1 Scope

- `yfinance` daily OHLCV data for a small US equity universe.
- Snapshot files with SHA-256 hashes.
- Point-in-time technical features.
- Temporal split, no random split.
- TP-before-SL labels with next-open execution.
- Logistic Regression / Random Forest baseline.
- Precomputed signal columns.
- Backtest with execution rules, slippage, commissions, and gap skips.
- Experiment log.
- Streamlit dashboard.
- Anti-lookahead tests.

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m src.pipeline
.\.venv\Scripts\streamlit run dashboard/app.py
```

## Important Limits

- `yfinance` is suitable for prototyping, not institutional validation.
- The MVP has survivorship bias.
- The MVP is not sufficient evidence for real capital allocation.
- All signals are research outputs, not financial advice.
