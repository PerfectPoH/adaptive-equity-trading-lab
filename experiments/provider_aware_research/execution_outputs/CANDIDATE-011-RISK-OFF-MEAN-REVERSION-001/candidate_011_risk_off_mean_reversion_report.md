# Candidate 011 Risk-Off Mean Reversion 001

Decision: `CANDIDATE_011_RISK_OFF_MEAN_REVERSION_ARCHIVE_NO_PROMOTION`

Scope: one fixed follow-up diagnostic for RISK_OFF mean reversion. No provider query, no parameter sweep, no promotion.

## IS/OOS Summary

- IS trades: `20`
- IS weighted net: `-0.0753394175357502`
- OOS trades: `19`
- OOS weighted net: `0.06586794899032468`
- OOS median net: `0.04353333624035231`
- OOS win rate: `0.7368421052631579`
- OOS max drawdown: `0.0`
- OOS ex-top3 weighted net: `0.011322359249125807`

## Benchmarks

- SPY OOS return: `0.25942132702077325`
- IWM OOS return: `0.3788868121679061`

## Blockers

- `diagnostic_only_same_dataset_as_discovery`
- `trial_limited_two_year_history`
- `oos_trade_count_below_threshold`
- `oos_does_not_beat_spy`
- `oos_does_not_beat_iwm`
