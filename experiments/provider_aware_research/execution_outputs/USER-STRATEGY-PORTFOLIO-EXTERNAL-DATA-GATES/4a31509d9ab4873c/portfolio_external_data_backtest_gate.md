# Portfolio True Backtest Data Gate: PORTFOLIO-TRUE-BACKTEST-DATA-GATE-4A31509D9AB4873C

- status: `BLOCKED_EXTERNAL_DATA_CONTRACT_REQUIRED`
- decision: `PORTFOLIO_TRUE_BACKTEST_BLOCKED_DATA_GATE`
- provider_query_allowed: `false`
- market_data_download_allowed: `false`
- backtest_allowed: `false`

## Required Before Backtest

- `survivorship_free_universe`
- `point_in_time_membership`
- `delisted_symbol_prices`
- `listing_and_delisting_dates`
- `split_dividend_adjusted_ohlcv`
- `component_specific_data_resolution`
- `provider_entitlement_manifest`
- `raw_payload_retention_policy`
- `benchmark_panel`

## Provider Candidates

- **CRSP/WRDS**: `preferred_but_currently_unavailable` - blocker `access_not_confirmed`
- **Norgate Data**: `candidate_requires_subscription` - blocker `subscription_and_license_not_confirmed`
- **Sharadar/Nasdaq Data Link**: `candidate_requires_entitlement_probe` - blocker `PIT_membership_and_delisted_coverage_not_verified`
- **Polygon/AlphaVantage/Yahoo free tiers**: `rejected_for_promotion` - blocker `active_only_or_missing_PIT_delisted_metadata`