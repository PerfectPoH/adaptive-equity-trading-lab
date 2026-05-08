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
- Lagged GDELT market-news context features.
- Temporal split, no random split.
- Purged temporal split for forward labels near train/validation/test boundaries.
- TP-before-SL labels with next-open execution.
- Logistic Regression / Random Forest baseline.
- Isotonic probability calibration fit on validation only.
- Precomputed signal columns.
- Backtest with execution rules, slippage, commissions, and gap skips.
- Per-run analysis for signal concentration, skipped trades, and benchmark underperformance.
- Probability calibration reports.
- Closed-trade error analysis.
- Feature-regime diagnostics for closed trades.
- Normalized equity curve export.
- Experiment log.
- Streamlit dashboard.
- Anti-lookahead tests.

## Run Locally

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.news_ablation
.\.venv-lab\Scripts\python.exe -m src.experiments.threshold_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.model_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.feature_set_comparison
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

The current default research baseline is `use_news=False`, `model_type=random_forest`, baseline feature set, isotonic-calibrated model probabilities, no regime filters, and `model_probability > 0.25`. Walk-forward validation selected the calibrated `0.25` variant for the 2024 test fold and improved the default 2024 strategy return to ~6.99%, while still underperforming buy-and-hold. Model and feature-set comparison currently keep Random Forest with the baseline features as the default; news features, enhanced context features, and regime filters remain analysis tools rather than defaults.

## Project Vault

The Obsidian-style project memory lives in `vault/`.

Start from `vault/INDEX.md`, then read `vault/00-Progetto/Memoria-AI.md` and `vault/00-Progetto/Roadmap-Master.md` before making structural changes.

## Important Limits

- `yfinance` is suitable for prototyping, not institutional validation.
- If a fresh `yfinance` download fails, the downloader can fall back to the latest local snapshot for reproducible experiments.
- GDELT news features are experimental macro-context features, lagged by one day to reduce leakage risk.
- The MVP has survivorship bias.
- The MVP is not sufficient evidence for real capital allocation.
- All signals are research outputs, not financial advice.
