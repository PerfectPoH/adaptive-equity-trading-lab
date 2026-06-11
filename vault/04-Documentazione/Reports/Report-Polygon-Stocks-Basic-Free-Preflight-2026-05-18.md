# Report - Polygon Stocks Basic Free Preflight - 2026-05-18

## Objective

Evaluate Polygon.io Stocks Basic Free as a no-cost secondary provider for recent US equities reference data and corporate actions, especially for gaps left by Databento Reference API subscription gating.

## Governance

```text
payment_authorized: false
payment_cap_usd: 0
raw_response_retention: disabled
all_symbols_query: not_used
rate_limit_control: 13 second delay between calls
api_key_source: .env / POLYGON_API_KEY
```

## Plan claim checked

User-provided plan features:

```text
Stocks Basic Free
0 USD/month
5 API calls/minute
2 years historical data
End of day data
Reference data
Corporate actions
Minute aggregate
```

## Micro-probe results

```text
checks_executed: 5
checks_passed: 4
```

| Event | Symbol | Capability | Result | Derived evidence |
|---|---|---|---|---|
| DPE-002 | MULN | reverse split reference | pass | splits endpoint returned 1 row |
| DPE-005 | WEYS | dividend reference | pass | dividends endpoint returned 2 rows |
| DPE-010 | DJT | ticker details reference | pass | ticker details returned 1 row |
| DPE-010 | DJT | minute aggregate | error | HTTP 403 |
| DPE-006 | FSR | delisted ticker details | pass | ticker details returned 1 row |

## Interpretation

Polygon Stocks Basic Free is useful as a secondary reference/corporate-actions cross-check for recent events. It is not a full provider replacement because minute aggregates were not available with the current free key in this probe and the 2-year historical limit remains a structural constraint.

## Verdict

```text
POLYGON_FREE_USEFUL_SECONDARY_REFERENCE_PROVIDER
NOT_FULL_OHLCV_PROVIDER_PASS
```

Recommended use:

```text
Databento Historical = OHLCV candidate
Polygon Free = recent corporate-actions/reference cross-check
Databento Reference or another paid/reference provider = still needed for final provider pass if full PIT/reference coverage is required
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
