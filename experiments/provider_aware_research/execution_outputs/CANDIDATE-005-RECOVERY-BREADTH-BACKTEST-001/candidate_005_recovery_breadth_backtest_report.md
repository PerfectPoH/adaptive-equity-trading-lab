# Candidate 005 Recovery Breadth Backtest 001

Decision: `CANDIDATE_005_RECOVERY_BREADTH_BACKTEST_ARCHIVE_NO_PROMOTION`

Scope: one trial-limited breadth-basket backtest. No parameter sweep, no promotion.

## Summary

- Trades: `37`.
- Weighted net return sum: `0.147262`.
- Win rate: `0.595`.
- Max drawdown: `-0.029436`.
- Best symbol: `FCEL`.
- Ex-best-symbol weighted net: `0.094271`.
- Top-symbol concentration: `0.35984001093389945`.

## Blockers

- `trial_history_window_limited`
- `promotion_locked_until_long_history_oos_gate`
- `single_symbol_concentration_above_30pct`
- `benchmark_relative_not_positive`
