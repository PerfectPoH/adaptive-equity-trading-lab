# Report - Provider Combo Gate: Databento Historical + Polygon Free - 2026-05-18

## Context

Databento Historical passed controlled OHLCV probes across the frozen DPE panel. Databento Reference API was confirmed to require an approximately `300 USD/month` subscription and was declined for now. Polygon Stocks Basic Free passed limited recent reference/corporate-action probes but failed a minute aggregate probe with HTTP 403.

## Decision

```text
PROVIDER_COMBO_GATE_APPROVED_FOR_DATA_QUALITY_AUDIT
NOT_APPROVED_FOR_STRATEGY_TRIALS_OR_BACKTESTS
```

## Provider roles

```text
Databento Historical: primary OHLCV candidate
Polygon Stocks Basic Free: secondary recent reference/corporate-actions cross-check
Databento Reference: technically suitable but economically blocked
```

## Allowed next phase

The next approved phase is a data-quality audit, not a performance experiment.

Allowed:

```text
DPE_PANEL_DERIVED_FEATURE_TABLE
EVENT_WINDOW_AVAILABILITY_MATRIX
CORPORATE_ACTION_CROSSCHECK_MATRIX
PROVIDER_JOIN_FEASIBILITY_CHECK
```

Blocked:

```text
BACKTEST
OOS
PARAMETER_SWEEP
LIVE_TRADING
PAPER_TRADING
RAW_PROVIDER_PAYLOAD_RETENTION
ALL_SYMBOLS_QUERY
```

## Remaining blockers for final provider pass

```text
adjustment_factors: blocked
full PIT universe: blocked
full security master: blocked
raw storage rights: unclear
Polygon historical depth: 2-year constraint
Polygon aggregate access: HTTP 403 observed in DJT minute probe
```

## Verdict

The Databento+Polygon combination is sufficient to begin a controlled data-quality audit against the frozen DPE panel. It is not sufficient to support any strategy performance claim.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
