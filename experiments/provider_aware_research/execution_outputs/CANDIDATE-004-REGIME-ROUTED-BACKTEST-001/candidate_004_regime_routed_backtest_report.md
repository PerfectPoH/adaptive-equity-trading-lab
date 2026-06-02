# Candidate 004 Regime-Routed Backtest 001

Decision: `CANDIDATE_004_REGIME_ROUTED_BACKTEST_ARCHIVE_NO_PROMOTION`

Scope: one trial-limited Norgate backtest under the pre-committed regime router. No parameter sweep, no promotion.

## Summary

- Trades: `14`.
- Weighted net return sum: `0.150406`.
- Win rate: `0.571`.
- Max drawdown: `-0.027512`.
- Best symbol: `FCEL`.
- Ex-best-symbol weighted net: `-0.000692`.

## Route Summary

- RECOVERY_BOUNCE / Mean Reversion: trades=6 weighted_net=0.007409 win_rate=0.500
- RECOVERY_BOUNCE / Momentum: trades=8 weighted_net=0.142997 win_rate=0.625

## Blockers

- `trial_history_window_limited`
- `promotion_locked_until_long_history_oos_gate`
- `sample_starved_regime_router`
- `outlier_dependency_ex_best_symbol_nonpositive`
- `benchmark_relative_not_positive`
