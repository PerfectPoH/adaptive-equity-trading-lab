---
tipo: xmom-real-data-ingestion
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Real Data Ingestion - 2026-05-20

## Scope

Performed the first real Databento data ingestion for `TRIAL-XMOM-001`.

This was data ingestion only. No backtest, sweep, paper trading, live trading or strategy promotion was executed.

## Output Directory

```text
experiments/provider_aware_research/data_inputs/databento_xmom_20260520/
```

Files:

```text
README.md
dataset_manifest.json
prices.csv
data_input_validation_report.json
```

## Dataset

Symbols:

```text
AEHR
ARRY
CABA
CRMD
IOVA
IWM
```

Provider datasets:

```text
XNAS.ITCH: AEHR, ARRY, CABA, CRMD, IOVA
ARCX.PILLAR: IWM
```

Schema:

```text
ohlcv-1d
```

Coverage:

```text
manifest_start: 2022-01-01
query_start: 2022-01-03
end: 2025-12-31
rows: 6012
rows_per_symbol: 1002
first_observed_date: 2022-01-03
last_observed_date: 2025-12-30
```

Raw payload retention:

```text
false
```

Only derived OHLCV CSV was retained.

## Caveats

Databento emitted reduced-quality/degraded-day warnings during ingestion.

Recorded examples:

```text
XNAS symbols: 2022-09-19 degraded
IWM / ARCX: 2022-07-18, 2022-08-22, 2022-12-05 degraded
```

These warnings are recorded in `dataset_manifest.json` under `provider_warnings`.

The dataset remains caveated:

- provider-default adjustment policy is not independently verified;
- Reference/PIT/corporate-action coverage remains governed by prior provider caveats;
- raw payloads were not retained.

## Data Ingestion Gate

Command:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_data_input_validator --data-dir experiments\provider_aware_research\data_inputs\databento_xmom_20260520 --write-report
```

Result:

```text
status: pass
gate_decision: DATA_INPUT_VALIDATION_PASS
passed: 17
failed: 0
```

Important checks:

```text
symbols_match_manifest: pass
symbol_date_coverage_matches_manifest: pass
no_duplicate_symbol_date: pass
prices_positive: pass
ohlc_relationships_valid: pass
close_to_close_return_within_sanity_threshold: pass
```

## XMOM Pre-Run Gate

Command:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_pre_run_gate_validator --gate-dir experiments\provider_aware_research\xmom_pre_run_gate_20260520
```

Result:

```text
status: pass
gate_decision: PASS_READY_TO_EXECUTE
passed: 17
failed: 0
```

Interpretation:

```text
The system is now technically ready for an explicitly authorized TRIAL-XMOM-001 execution.
This report does not authorize execution by itself.
```

## Status

```text
REAL_DATA_INGESTION_COMPLETE
DATA_INPUT_VALIDATION_PASS
PRE_RUN_GATE_PASS_READY_TO_EXECUTE
NO_BACKTEST
NO_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_OR_LIVE_TRADING
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
