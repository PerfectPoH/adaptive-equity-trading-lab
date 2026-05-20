---
tipo: data-ingestion-gate
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: SPEC_AND_VALIDATOR_COMPLETE
---

# Report XMOM Data Ingestion Gate - 2026-05-20

## Scope

Implemented the data-ingestion validator required before `TRIAL-XMOM-001` can move from preregistered plan to executable run.

The goal is to treat incoming provider data as untrusted until validated.

## Validator

```text
src.experiments.xmom_data_input_validator
```

CLI:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_data_input_validator --data-dir experiments\provider_aware_research\data_inputs\databento_xmom_20260520 --write-report
```

The validator writes:

```text
data_input_validation_report.json
```

## Required Manifest

The data directory must contain:

```text
dataset_manifest.json
```

The manifest must declare:

- dataset id;
- provider and provider dataset;
- request lineage and API configuration;
- timezone;
- price adjustment policy;
- raw-payload retention policy;
- immutable-after-validation flag;
- expected symbols;
- date range;
- sanity thresholds;
- declared data files and SHA-256 hashes.

## Data Checks

- all declared files exist and match SHA-256;
- OHLCV schema contains `symbol,date,open,high,low,close,volume`;
- observed symbols match `expected_symbols`;
- dates parse and stay inside the declared range;
- each expected symbol covers the declared start/end within configured trading-calendar tolerances;
- no duplicate `symbol/date`;
- prices are finite and positive;
- volume is finite and non-negative;
- OHLC relationships are valid;
- intraday range and close-to-close returns stay inside sanity thresholds.

## Pre-Run Gate Hardening

`xmom_pre_run_gate_validator.py` no longer accepts arbitrary files in the Databento data directory.

It now requires:

```text
data_input_validation_report.json
status: pass
gate_decision: DATA_INPUT_VALIDATION_PASS
```

Therefore, the pre-run gate remains fail-closed until the data-ingestion validator passes.

## Status

```text
SPEC_AND_VALIDATOR_COMPLETE
NO_PROVIDER_QUERY
NO_DATA_INGESTED
NO_BACKTEST
NO_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_OR_LIVE_TRADING
```
