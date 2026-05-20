# 2026-05-20 - XMOM real data ingestion

## Contesto

Dopo il synthetic dry run del Data Ingestion Gate, e' stata eseguita l'ingestione reale Databento per `TRIAL-XMOM-001`.

## Cosa e' stato fatto

Creata directory reale:

```text
experiments/provider_aware_research/data_inputs/databento_xmom_20260520/
```

Contenuto:

```text
README.md
dataset_manifest.json
prices.csv
data_input_validation_report.json
```

Dataset usati:

```text
XNAS.ITCH: AEHR, ARRY, CABA, CRMD, IOVA
ARCX.PILLAR: IWM
```

Motivo: `EQUS.MINI` parte dal 2023-03-28 e non copre la finestra preregistrata 2022+.

## Risultati ingestione

```text
symbols: 6
rows: 6012
rows_per_symbol: 1002
first_observed_date: 2022-01-03
last_observed_date: 2025-12-30
raw_payload_retention: false
```

Databento ha emesso warning su giornate degraded nel 2022; la caveat e' registrata nel manifest.

## Data Gate

```text
DATA_INPUT_VALIDATION_PASS
passed: 17
failed: 0
```

## Pre-Run Gate

```text
PASS_READY_TO_EXECUTE
passed: 17
failed: 0
```

## Decisione

Il progetto e' pronto per chiedere autorizzazione esplicita all'esecuzione di `TRIAL-XMOM-001`.

Questa sessione non ha eseguito backtest, sweep, paper trading, live trading o promozione strategica.

Vedi [[Report-XMOM-Real-Data-Ingestion-2026-05-20]], [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]], [[Project-Handoff]].
