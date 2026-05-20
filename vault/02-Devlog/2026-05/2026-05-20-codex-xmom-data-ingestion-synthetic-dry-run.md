# 2026-05-20 - XMOM data-ingestion synthetic dry run

## Contesto

Dopo il Data Ingestion Gate, serviva provare la catena su un dataset minuscolo senza toccare la directory reale `databento_xmom_20260520`.

## Cosa e' stato fatto

Creata directory isolata:

```text
experiments/provider_aware_research/xmom_data_ingestion_synthetic_dry_run_20260520/
```

Contiene dati sintetici OHLCV per `AAA` e `BBB`, manifest con hash e report di validazione.

## Verifica Data Gate

Comando:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.xmom_data_input_validator --data-dir experiments\provider_aware_research\xmom_data_ingestion_synthetic_dry_run_20260520 --write-report
```

Risultato:

```text
DATA_INPUT_VALIDATION_PASS
passed: 16
failed: 0
```

## Verifica isolamento

Il pre-run gate reale `TRIAL-XMOM-001` resta bloccato:

```text
BLOCKED_EXIT_1
runtime_databento_data_exists: fail
```

## Decisione

Il dry run prova il meccanismo ma non sblocca alcuna ricerca reale. Il prossimo step resta ingestione reale Databento nella directory ufficiale, seguita dal validator.

Vedi [[Report-XMOM-Data-Ingestion-Synthetic-Dry-Run-2026-05-20]], [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]].
