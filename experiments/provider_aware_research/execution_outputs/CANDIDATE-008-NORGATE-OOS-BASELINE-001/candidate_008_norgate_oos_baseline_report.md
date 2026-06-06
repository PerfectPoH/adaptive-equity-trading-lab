# Candidate 008 Norgate OOS Baseline 001

Decision: `CANDIDATE_008_NORGATE_OOS_BASELINE_ARCHIVE_NO_PROMOTION`

Scope: one fixed diagnostic backtest on Candidate 007. No provider query, no sweep, no promotion.

## IS/OOS Summary

- IS trades: `68`
- IS weighted net: `-0.4772755953645461`
- OOS trades: `89`
- OOS weighted net: `-0.045000242565343504`
- OOS win rate: `0.449438202247191`
- OOS max drawdown: `-0.2587217382381713`

## Benchmarks

- SPY OOS return: `0.25942132702077325`
- IWM OOS return: `0.3788868121679061`

## Blockers

- `diagnostic_only_no_promotion`
- `trial_limited_two_year_history`
- `oos_weighted_net_nonpositive`
- `oos_ex_top3_weighted_net_nonpositive`
- `oos_does_not_beat_spy`
- `oos_does_not_beat_iwm`
