# Candidate 006 Kronos Overlay Backtest 001

Decision: `CANDIDATE_006_KRONOS_OVERLAY_BACKTEST_ARCHIVE_NO_PROMOTION`

Scope: one frozen sign-filter overlay backtest. No threshold optimization, no reranking, no promotion.

## Summary

- Baseline trades: `37`
- Overlay kept trades: `11`
- Cash-routed trades: `26`
- Baseline weighted net: `0.14726152684605037`
- Overlay weighted net: `0.05342042500865488`
- Overlay minus baseline: `-0.0938411018373955`
- Overlay max drawdown: `-0.0003614772957769002`
- Overlay win rate: `0.8181818181818182`

## Robustness

- Best symbol: `FCEL`
- Ex-best-symbol overlay net: `0.02320072889553528`
- Top-symbol concentration: `0.5656955388921666`

## Blockers

- `promotion_locked_until_separate_oos_gate`
- `single_trial_overlay_diagnostic_only`
- `overlay_trade_count_below_30`
- `overlay_top_symbol_concentration_above_30pct`
