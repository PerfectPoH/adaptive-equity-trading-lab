# XMOM Data Ingestion Gate

```text
XMOM_DATA_INGESTION_GATE_DEFINED
SPEC_ONLY_NO_DATA_INGESTED
FAIL_CLOSED
```

This gate validates provider-aware XMOM input data before `TRIAL-XMOM-001` can pass the pre-run gate.

The intended data directory is:

```text
experiments/provider_aware_research/data_inputs/databento_xmom_20260520/
```

The directory must contain:

```text
dataset_manifest.json
prices.csv or declared OHLCV files
data_input_validation_report.json
```

The validation report must be produced by:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_data_input_validator --data-dir experiments\provider_aware_research\data_inputs\databento_xmom_20260520 --write-report
```

The XMOM pre-run gate must remain blocked until `data_input_validation_report.json` has:

```text
status: pass
gate_decision: DATA_INPUT_VALIDATION_PASS
```

This spec performs no provider query, no backtest, no sweep, no paper trading and no live trading.
