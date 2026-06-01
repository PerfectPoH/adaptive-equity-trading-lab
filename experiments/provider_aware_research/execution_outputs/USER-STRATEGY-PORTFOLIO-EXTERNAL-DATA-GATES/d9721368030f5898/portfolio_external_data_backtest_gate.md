# Portfolio True Backtest Data Gate: PORTFOLIO-CANDIDATE-003-DATA-GATE-D9721368030F5898

- status: `BLOCKED_EXTERNAL_DATA_CONTRACT_REQUIRED`
- decision: `PORTFOLIO_CANDIDATE_003_TRUE_BACKTEST_BLOCKED_DATA_GATE`
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

- **Norgate Data**: `local_trial_installed_requires_schema_probe` - blocker `norgate_python_schema_and_trial_history_window_not_verified_for_this_candidate`
- **CRSP/WRDS**: `preferred_but_currently_unavailable` - blocker `access_not_confirmed`
- **Sharadar/Nasdaq Data Link**: `candidate_requires_entitlement_probe` - blocker `PIT_membership_and_delisted_coverage_not_verified`
- **Polygon/AlphaVantage/Yahoo free tiers**: `rejected_for_promotion` - blocker `active_only_or_missing_PIT_delisted_metadata`

## Next Allowed Step

Run a schema-only Norgate probe for Candidate 003. The probe may inspect installed package availability, symbol mapping, delisted coverage fields, adjustment fields, and available history windows. It must not run the portfolio candidate backtest until this gate is satisfied and committed.

The current gate intentionally leaves `provider_query_allowed`, `market_data_download_allowed`, and `backtest_allowed` set to `false`.
