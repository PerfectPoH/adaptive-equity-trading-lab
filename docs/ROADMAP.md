# Roadmap

## Milestone 1: Prototype Core

Build the smallest honest end-to-end pipeline.

Definition of done:

1. Downloads daily data for 10 tickers.
2. Handles basic `yfinance` retries/errors.
3. Saves snapshots with hashes.
4. Validates data integrity.
5. Computes point-in-time features.
6. Builds TP-before-SL labels with next-open entry and purged split boundaries.
7. Trains a baseline model.
8. Calibrates probabilities on validation only.
9. Generates signals.
10. Runs a backtest.
11. Shows a Streamlit dashboard.
12. Logs experiments to CSV.
13. Passes minimum anti-lookahead tests.
14. Beats buy-and-hold out-of-sample or documents why it does not.

## Later Milestones

- Research validation: calibrated walk-forward folds, model comparison, feature-set comparison, target/exit comparison, signal-quality/ranking comparison, market-exposure comparison, model registry, optional risk-first modes.
- News/context: news risk filter, Graphify, manual Markdown vault.
- Paper trading: Alpaca/IBKR paper with manual confirmation.
- Realism upgrade: better data, spread checks, volume limits, tax-aware returns.
- Institutional gate: point-in-time data, event-driven backtesting, DSR, CPCV, capacity analysis.
- Small live manual: only after validation, with kill switches and tiny capital.
