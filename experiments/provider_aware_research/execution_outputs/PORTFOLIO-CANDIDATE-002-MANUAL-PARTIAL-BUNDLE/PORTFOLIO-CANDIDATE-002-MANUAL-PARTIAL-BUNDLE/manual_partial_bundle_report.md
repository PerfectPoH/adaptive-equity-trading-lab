# Manual Partial Data Bundle

- bundle_id: `PORTFOLIO-CANDIDATE-002-MANUAL-PARTIAL-BUNDLE`
- status: `MANUAL_PARTIAL_DATA_BUNDLE_EXPLORATORY_ONLY`
- runner status: `NO_REAL_DATA_NO_CLAIM`
- exploratory only: `true`
- real financial claim allowed: `false`
- portfolio backtest performed: `false`

## Covered Fields

- `split_dividend_adjusted_ohlcv`
- `benchmark_panel`
- `tradability_and_liquidity_history`
- `raw_payload_retention_manifest`

## Missing Fields Declared Upfront

- `survivorship_free_universe`
- `point_in_time_membership`
- `listing_and_delisting_dates`
- `delisted_symbol_prices`

This artifact is the no-capital fallback path. It can test interfaces, not alpha.