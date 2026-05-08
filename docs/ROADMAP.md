# Roadmap

## Milestone 1: Prototype Core

Build the smallest honest end-to-end pipeline.

Definition of done:

1. Downloads daily data for 10 tickers.
2. Handles basic `yfinance` retries/errors.
3. Saves snapshots with hashes.
4. Validates data integrity.
5. Computes point-in-time features.
6. Builds TP-before-SL labels with next-open entry.
7. Trains a baseline model.
8. Generates signals.
9. Runs a backtest.
10. Shows a Streamlit dashboard.
11. Logs experiments to CSV.
12. Passes minimum anti-lookahead tests.
13. Beats buy-and-hold out-of-sample or documents why it does not.

## Later Milestones

- Research validation: walk-forward, broader threshold sweeps, feature-regime error analysis, calibrated-risk interpretation, optional risk-first modes.
- News/context: news risk filter, Graphify, manual Markdown vault.
- Paper trading: Alpaca/IBKR paper with manual confirmation.
- Realism upgrade: better data, spread checks, volume limits, tax-aware returns.
- Institutional gate: point-in-time data, event-driven backtesting, DSR, CPCV, capacity analysis.
- Small live manual: only after validation, with kill switches and tiny capital.
