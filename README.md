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
- Per-run analysis for signal concentration, skipped trades, and benchmark underperformance.
- Normalized equity curve export.
- Experiment log.
- Streamlit dashboard.
- Anti-lookahead tests.

## Run Locally

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

## Project Vault

The Obsidian-style project memory lives in `vault/`.

Start from `vault/INDEX.md`, then read `vault/00-Progetto/Memoria-AI.md` and `vault/00-Progetto/Roadmap-Master.md` before making structural changes.

## Important Limits

- `yfinance` is suitable for prototyping, not institutional validation.
- The MVP has survivorship bias.
- The MVP is not sufficient evidence for real capital allocation.
- All signals are research outputs, not financial advice.
