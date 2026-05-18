# Provider combo gate - Databento Historical + Polygon Stocks Basic Free

## Decision

```text
PROVIDER_COMBO_GATE_APPROVED_FOR_DATA_QUALITY_AUDIT
NOT_APPROVED_FOR_STRATEGY_TRIALS_OR_BACKTESTS
```

## Approved provider roles

| Capability | Provider | Status |
|---|---|---|
| Historical OHLCV bars | Databento Historical / EQUS.MINI | approved for data-quality audit input |
| Limited trades probe | Databento Historical / EQUS.MINI | approved for diagnostics only |
| Recent splits/dividends | Polygon Stocks Basic Free | approved for cross-check only |
| Recent ticker/reference details | Polygon Stocks Basic Free | approved for cross-check only |
| Adjustment factors | none | blocked |
| Full PIT universe | none | blocked |
| Full security master | none | blocked |
| Raw response storage | none | blocked until license rights confirmed |

## Allowed next work

```text
DATA_QUALITY_AUDIT_DESIGN
DPE_PANEL_DERIVED_FEATURE_TABLE
EVENT_WINDOW_AVAILABILITY_MATRIX
CORPORATE_ACTION_CROSSCHECK_MATRIX
PROVIDER_JOIN_FEASIBILITY_CHECK
```

## Disallowed work

```text
NO_BACKTEST
NO_OUT_OF_SAMPLE_TEST
NO_PARAMETER_SWEEP
NO_LIVE_TRADING
NO_PAPER_TRADING
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_ALL_SYMBOLS_QUERY
```

## Minimum controls

1. Use only frozen DPE event IDs unless a new panel expansion report is created.
2. Query only event symbols and narrow windows.
3. Store derived metadata only: counts, hashes, field names, availability flags and verdicts.
4. Keep provider-specific caveats attached to every downstream feature table.
5. Treat missing adjusted/PIT/reference coverage as a blocker for any strategy performance claim.

## Stop conditions

Stop and re-evaluate if any of the following occurs:

```text
Provider requires paid upgrade for planned query
Provider response contradicts documented availability
Rate limit blocks repeatability
Raw storage becomes necessary
A downstream step attempts strategy/backtest/OOS/sweep/live/paper trading
```

## Current final status

```text
Databento Historical: usable OHLCV candidate
Polygon Free: useful secondary recent reference provider
Provider combo: usable for data-quality audit only
Final provider pass: no
```
