# Norgate Candidate 003 Micro-Backtest 001

- decision: `NORGATE_CANDIDATE_003_MICRO_BACKTEST_ARCHIVE_NO_PROMOTION`
- bundle: `NORGATE-CANDIDATE-003-ADMISSIBLE-MICRO-BUNDLE-001`
- trial limited: `true`
- total trades: `43`
- weighted net return sum: `0.105438`
- max drawdown: `-0.197706`
- ex-best-symbol weighted net return: `-0.023540`
- active symbols: `5`
- delisted symbols: `12`

## Tradability Filter

- accepted symbols after filter: `19`
- tradability rejections: `43`
- minimum price: `1.0`
- minimum median turnover: `1000000.0`

## Disabled Sleeves

- `Catalyst`: missing_point_in_time_event_and_direction_source
- `Dollar-Bar Microstructure`: daily_bars_cannot_reconstruct_dollar_bars

## Final Blockers

- `trial_history_window_limited`
- `trial_history_below_full_validation_requirement`
- `promotion_locked_until_long_history_oos_gate`
- `Catalyst:missing_point_in_time_event_and_direction_source`
- `Dollar-Bar Microstructure:daily_bars_cannot_reconstruct_dollar_bars`
- `outlier_dependency_ex_best_symbol_nonpositive`
- `weak_distribution_win_rate_below_half`
- `daily_only_dollar_bar_sleeve_disabled`

No promotion, paper trading, live trading, parameter sweep, or durable financial performance claim is allowed from this trial-limited run.

## Candidate 003 Notes

- This run used the Candidate 003 micro-backtest gate, not the older Candidate 002 gate.
- Dollar-Bar Microstructure remained disabled/idle because daily Norgate bars cannot reconstruct dollar bars.
- Disabled sleeve weight was not redistributed.
- Trial limitation remains binding: no promotion or financial performance claim.
