# Polygon Stocks Basic Free provider evaluation summary

Status: `PREFLIGHT_CREATED_NOT_EXECUTED`.

Governance: no raw retention, no ALL_SYMBOLS, no payment authorization, 5 calls/minute respected.

## Polygon free micro-probe update

```text
PROVIDER_QUERY_EXECUTED
checks_executed: 5
checks_passed: 4
executed_at_utc: 2026-05-18T09:44:38.283414+00:00
raw_response_retention: disabled
rate_limit_control: sleep between calls
```

## Polygon Stocks Basic Free verdict

```text
POLYGON_FREE_MICRO_PROBE_EXECUTED
checks_executed: 5
checks_passed: 4
reference_splits: pass; MULN rows=1
reference_dividends: pass; WEYS rows=2
ticker_details_DJT: pass; rows=1
ticker_details_FSR: pass; rows=1
minute_aggregate_DJT: HTTP_ERROR_403
raw_response_retention: disabled
provider_verdict: USEFUL_SECONDARY_REFERENCE_PROVIDER_NOT_FULL_OHLCV_PROVIDER
```

Polygon Stocks Basic Free is useful as a secondary reference/corporate-actions cross-check for recent events. It is not a full replacement for Databento OHLCV because the controlled minute aggregate probe returned HTTP 403 and the 2-year historical limit remains a structural caveat.
