# Devlog - Provider combo gate - 2026-05-18

## Decision

```text
PROVIDER_COMBO_GATE_APPROVED_FOR_DATA_QUALITY_AUDIT
NOT_APPROVED_FOR_STRATEGY_TRIALS_OR_BACKTESTS
```

## Provider roles

```text
Databento Historical: OHLCV candidate
Polygon Stocks Basic Free: secondary recent reference/corporate-actions cross-check
Databento Reference: blocked by 300 USD/month subscription, declined for now
```

## Allowed next work

```text
DPE_PANEL_DERIVED_FEATURE_TABLE
EVENT_WINDOW_AVAILABILITY_MATRIX
CORPORATE_ACTION_CROSSCHECK_MATRIX
PROVIDER_JOIN_FEASIBILITY_CHECK
```

Blocked: backtest, OOS, sweep, live, paper trading, raw retention, ALL_SYMBOLS.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
