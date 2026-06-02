# Norgate Candidate 003 Second Backtest 001

- decision: `NORGATE_CANDIDATE_003_SECOND_BACKTEST_ARCHIVE_NO_PROMOTION`
- total trades: `61`
- weighted net return sum: `0.490214`
- gross return sum: `2.570855`
- win rate: `0.3770`
- max drawdown: `-0.785637`
- best symbol: `TERN-202605`
- best-symbol weighted net: `0.632019`
- ex-best-symbol weighted net: `-0.141806`
- max single-symbol trade share: `0.0820`
- frames loaded non-benchmark: `282`
- accepted active: `159`
- accepted delisted: `123`

## Benchmark Relative

- `SPY` total return: `0.472147296238407`; strategy minus benchmark: `0.018066399514174714`
- `IWM` total return: `0.4439339217762772`; strategy minus benchmark: `0.046279773976304506`

## Component Contributions

- `9474fe601e0f2bd2` / `Dollar-Bar Microstructure` / `disabled_idle`: trades `0`, weighted net `0.000000`
- `28fb7b03aa56a91e` / `Momentum` / `active`: trades `21`, weighted net `0.328463`
- `a42078cbf0a2ea94` / `Mean Reversion` / `active`: trades `19`, weighted net `-0.166712`
- `acc065823d9dcfb7` / `Momentum` / `active`: trades `21`, weighted net `0.328463`

## Final Blockers

- `trial_history_window_limited`
- `promotion_locked_until_long_history_oos_gate`
- `Dollar-Bar Microstructure:daily_bars_cannot_reconstruct_dollar_bars`
- `outlier_dependency_ex_best_symbol_nonpositive`
- `weak_distribution_win_rate_below_half`
- `duplicated_momentum_component_correlation_risk`

No promotion, paper trading, live trading, parameter sweep, universe rebuild, or durable financial performance claim is allowed from this trial-limited run.