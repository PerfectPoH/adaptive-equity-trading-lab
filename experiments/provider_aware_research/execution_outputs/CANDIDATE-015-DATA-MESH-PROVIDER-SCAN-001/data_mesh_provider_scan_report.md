# Candidate 015 Data Mesh Provider Scan

Decision: `DATA_MESH_PROVIDER_SCAN_COMPLETE_NO_QUERY`

Scope: no-query provider architecture scan. This does not authorize provider calls, dataset builds, backtests, or promotion.

## Provider Matrix

| Provider | Status | Blockers | Next probe |
|---|---|---|---|
| Norgate Data Full US Stocks Platinum | `ADMISSIBLE_IF_SUBSCRIBED` | `subscription_required` | No probe needed if subscription is active; run fresh-data build gate directly. |
| CRSP/WRDS | `ADMISSIBLE_IF_ACCESS_GRANTED` | `institutional_access_required` | Verify account access and export licensing before any extraction. |
| Databento Historical + Reference | `BLOCKED_REFERENCE_ENTITLEMENT` | `databento_reference_entitlement_missing` | Only retry after Reference entitlement changes. |
| Norgate Trial | `BLOCKED_HISTORY_DEPTH` | `history_span_below_5_years` | No further trial probe; upgrade to full history or stop. |
| Tiingo | `REQUIRES_MICRO_PROBES` | `delisted_coverage_unverified`, `permanent_identity_mapping_unverified`, `license_cache_policy_unverified` | Bounded Tiingo active/split/ticker-change/delisted micro-probe. |
| EODHD | `REQUIRES_MICRO_PROBES` | `terminal_return_policy_unverified`, `corporate_action_policy_unverified`, `license_cache_policy_unverified` | Bounded delisted endpoint plus terminal OHLCV continuity micro-probe. |
| SimFin | `REQUIRES_MICRO_PROBES` | `coverage_breadth_unverified`, `price_history_sufficiency_unverified`, `license_cache_policy_unverified` | Bounded PIT metadata and delisted availability probe. |
| Financial Modeling Prep | `REQUIRES_MICRO_PROBES` | `legacy_endpoint_status_unverified`, `delisted_quality_unverified`, `license_cache_policy_unverified` | Bounded SPY/IWM and delisted endpoint availability probe. |
| SEC EDGAR | `REQUIRES_MICRO_PROBES` | `form25_parser_not_validated`, `terminal_price_not_provided`, `rate_limit_policy_required` | One CIK/Form 25 bounded parser probe with SEC-compliant User-Agent. |
| Hybrid Free Data Mesh | `REQUIRES_MICRO_PROBES` | `identity_reconciliation_unverified`, `delisted_terminal_return_unverified`, `corporate_action_policy_unverified`, `licensing_and_cache_policy_unverified`, `component_disagreement_resolution_unbuilt` | Do not probe the mesh directly; probe each component first. |

## Micro-Probe Plan

- `ACTIVE_BASELINE_AAPL`: Verify active OHLCV depth, adjusted fields, split/dividend metadata, and license/cache policy. Providers: Tiingo, EODHD, FMP.
- `SPLIT_AAPL_2020`: Verify split factor handling and adjusted/raw price consistency around a known split. Providers: Tiingo, EODHD, FMP.
- `TICKER_CHANGE_FB_META`: Verify identity continuity across a known ticker change. Providers: Tiingo, SEC EDGAR, SimFin.
- `DELISTING_BBBY`: Verify delisted price continuity and terminal date handling. Providers: EODHD, FMP, SEC EDGAR, Tiingo.
- `BENCHMARK_SPY_IWM`: Verify benchmark adjusted OHLCV depth and dividend treatment. Providers: Tiingo, FMP, EODHD.

## Decision

- Candidate 012 backtest remains blocked.
- Hybrid Free Data Mesh is not trusted until component-level micro-probes pass.
- Norgate Full or CRSP/WRDS remain the cleanest paths if access becomes available.
