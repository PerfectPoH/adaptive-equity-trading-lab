# Candidate 009 Regime Momentum 001

Decision: `CANDIDATE_009_REGIME_MOMENTUM_ARCHIVE_NO_PROMOTION`

Scope: one post-autopsy diagnostic backtest. It only routes momentum_60d through RECOVERY_BOUNCE and DRAWDOWN_STRESS.
No provider query, no parameter sweep, no Kronos inference, no promotion.

## IS/OOS Summary

- IS trades: `5`
- IS weighted net: `-0.1004025700714518`
- OOS trades: `10`
- OOS weighted net: `0.16877754635565315`
- OOS win rate: `0.4`
- OOS max drawdown: `-0.0016833850082071944`
- OOS ex-top3 weighted net: `-0.09238103986086571`

## Benchmarks

- SPY OOS return: `0.25942132702077325`
- IWM OOS return: `0.3788868121679061`

## Route Summary

- `is` / `DRAWDOWN_STRESS`: trades `5`, weighted net `-0.1004025700714518`, win rate `0.0`
- `oos` / `DRAWDOWN_STRESS`: trades `2`, weighted net `0.11562899906454628`, win rate `0.5`
- `oos` / `RECOVERY_BOUNCE`: trades `8`, weighted net `0.05314854729110688`, win rate `0.375`

## Blockers

- `diagnostic_only_post_autopsy_same_panel`
- `trial_limited_two_year_history`
- `oos_trade_count_below_threshold`
- `oos_ex_top3_weighted_net_nonpositive`
- `oos_does_not_beat_spy`
- `oos_does_not_beat_iwm`
