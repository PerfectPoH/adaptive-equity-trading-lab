# Norgate Portfolio Trial Backtest 001

- decision: `NORGATE_TRADABILITY_RERUN_ARCHIVE_NO_PROMOTION`
- bundle: `NORGATE-ADMISSIBLE-DATA-BUNDLE-001`
- trial limited: `true`
- total trades: `43`
- weighted net return sum: `-0.662664`
- max drawdown: `-0.638019`
- ex-best-symbol weighted net return: `-0.715254`
- active symbols: `26`
- delisted symbols: `31`

## Tradability Filter

- accepted symbols after filter: `59`
- tradability rejections: `103`
- minimum price: `1.0`
- minimum median turnover: `1000000.0`

## Disabled Sleeves

- `Catalyst`: missing_point_in_time_event_and_direction_source
- `Dollar-Bar Microstructure`: daily_bars_cannot_reconstruct_dollar_bars

## Final Blockers

- `trial_history_below_full_validation_requirement`
- `promotion_locked_until_long_history_oos_gate`
- `Catalyst:missing_point_in_time_event_and_direction_source`
- `Dollar-Bar Microstructure:daily_bars_cannot_reconstruct_dollar_bars`
- `outlier_dependency_ex_best_symbol_nonpositive`
- `weak_distribution_win_rate_below_half`

No promotion, paper trading, live trading, parameter sweep, or durable financial performance claim is allowed from this trial-limited run.