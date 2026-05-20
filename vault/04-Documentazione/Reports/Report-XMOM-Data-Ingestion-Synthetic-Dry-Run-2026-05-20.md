---
tipo: data-ingestion-synthetic-dry-run
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Data Ingestion Synthetic Dry Run - 2026-05-20

## Scope

Executed an isolated synthetic dry run for the XMOM data-ingestion gate.

This was not real provider data and does not unblock `TRIAL-XMOM-001`.

## Artifact

```text
experiments/provider_aware_research/xmom_data_ingestion_synthetic_dry_run_20260520/
```

Files:

```text
README.md
dataset_manifest.json
prices.csv
data_input_validation_report.json
```

## Validation Command

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_data_input_validator --data-dir experiments\provider_aware_research\xmom_data_ingestion_synthetic_dry_run_20260520 --write-report
```

Result:

```text
status: pass
gate_decision: DATA_INPUT_VALIDATION_PASS
passed: 16
failed: 0
```

## Real XMOM Pre-Run Gate Check

The real XMOM pre-run gate was rerun after the synthetic pass.

Result:

```text
status: fail
gate_decision: BLOCKED_EXIT_1
failed check: runtime_databento_data_exists
```

Interpretation:

```text
The data-ingestion validator works.
The real TRIAL-XMOM-001 gate remains blocked until the real Databento input directory has its own passing validation report.
```

## Governance Meaning

This dry run validates the gate mechanics only. It does not authorize:

- provider query;
- backtest;
- sweep;
- paper trading;
- live trading;
- strategy promotion.
