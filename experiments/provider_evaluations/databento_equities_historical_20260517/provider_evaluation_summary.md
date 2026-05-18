# Provider Evaluation Summary - Databento Equities Historical

```text
MICRO_PROBE_EXECUTED
PROVIDER_DATA_PARTIALLY_EVALUATED_ONE_EVENT_ONLY
RAW_RESPONSE_RETENTION_NOT_ENABLED
NO_PRICING_DECISION
NO_STRATEGY_TRIAL_OPENED
NO_BACKTEST / NO_OOS / NO_SWEEP
```

This directory records a Databento Equities Historical provider-evaluation micro-probe.

It exists to verify that the provider-evaluation artifacts can record a controlled one-event Databento probe.

The first probe returned 10 records for `DPE-006 / FSR` from `EQUS.MINI` using schema `trades`.

The follow-up OHLCV probe returned 5 one-minute bars for the same symbol/window using schema `ohlcv-1m`.

No raw provider payload is retained in the repository.

## One-event micro-probe update

```text
PROVIDER_QUERY_EXECUTED
event_id: DPE-006
dataset: EQUS.MINI
schema: trades
symbol: FSR
start: 2024-03-20T14:30
end: 2024-03-20T14:35
limit: 10
records_returned: 10
executed_at_utc: 2026-05-18T08:26:54.538690+00:00
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
```

## One-event OHLCV micro-probe update

```text
PROVIDER_QUERY_EXECUTED
event_id: DPE-006
dataset: EQUS.MINI
schema: ohlcv-1m
symbol: FSR
start: 2024-03-20T14:30
end: 2024-03-20T14:35
limit: 10
records_returned: 5
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
```

## Minimal full-panel readiness probe

```text
MINIMAL_FULL_PANEL_MICRO_PROBES_EXECUTED
DPE-001 TUP  ohlcv-1d  records=2
DPE-002 MULN ohlcv-1m  records=5
DPE-003 CNGL ohlcv-1d  records=4
DPE-004 ABAT ohlcv-1m  records=5
DPE-005 WEYS ohlcv-1d  records=8
DPE-006 FSR  trades+ohlcv-1m records=10+5
DPE-007 PHUN ohlcv-1m  records=5
DPE-008 GH   ohlcv-1d  records=6
DPE-009 ICU  ohlcv-1m  records=2
DPE-010 DWAC/DJT ohlcv-1d+ohlcv-1m records=3+5
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
```

All frozen DPE events now have minimal Databento symbol resolution and OHLCV/event-window evidence.

This is sufficient to proceed to a controlled full-panel evaluation pass.

This is not a final provider pass because adjusted OHLCV, corporate-action metadata, halt/suspension metadata, point-in-time universe support and license/storage rights remain caveated or untested.
