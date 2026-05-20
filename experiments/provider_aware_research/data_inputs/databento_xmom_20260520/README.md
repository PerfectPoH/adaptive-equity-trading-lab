# Databento XMOM Data Input - 2026-05-20

```text
REAL_PROVIDER_DERIVED_DATA
DATA_INPUT_VALIDATION_PASS
PRE_RUN_GATE_PASS_READY_TO_EXECUTE
NO_BACKTEST_EXECUTED_BY_THIS_INGESTION
```

This directory contains derived daily OHLCV data for `TRIAL-XMOM-001`.

Raw Databento payloads were not retained. The dataset uses venue-specific Databento datasets to cover the preregistered 2022+ window:

- `XNAS.ITCH`: `AEHR`, `ARRY`, `CABA`, `CRMD`, `IOVA`
- `ARCX.PILLAR`: `IWM`

Known caveat: Databento emitted reduced-quality/degraded-day warnings during ingestion. These are recorded in `dataset_manifest.json` under `provider_warnings`.

This data input is necessary but not sufficient for strategy execution. Execution still requires explicit run authorization and all relevant gates.
