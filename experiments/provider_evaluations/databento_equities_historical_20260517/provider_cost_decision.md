# Databento Reference API cost decision

## User-reported provider response

Databento support confirmed that Reference API access requires a paid subscription priced at approximately:

```text
300 USD/month
```

## Decision

```text
DATABENTO_REFERENCE_SUBSCRIPTION_DECLINED_FOR_NOW
```

## Rationale

Databento Historical OHLCV access is already usable for controlled historical bar/trade probes, but the Reference API subscription is not justified during provider preflight and data-quality gate construction.

## Updated provider role

```text
Databento Historical = OHLCV historical provider candidate
Databento Reference = technically suitable but economically blocked
Polygon Stocks Basic Free = secondary recent reference/corporate-actions cross-check
```

## Final Databento status for current phase

```text
HISTORICAL_OHLCV_PROVIDER_CANDIDATE
REFERENCE_DATA_BLOCKED_BY_PAID_SUBSCRIPTION
NOT_FULL_PROVIDER_PASS
```

## Revisit condition

Reconsider the 300 USD/month Reference subscription only if the project reaches a stage where full PIT/reference coverage is required and expected research value or revenue justifies the recurring cost.
