---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-metadata-builder
tags: [devlog, small-cap, metadata, watchlist, cli, tdd]
---

# 2026-05-10 - Small-Cap Metadata Builder

## Contesto

La CLI esperimento small-cap richiede un CSV statico con `symbol`, `market_cap` e `is_etf`. Per evitare valori inventati o hardcoded, e' stato aggiunto un builder testabile che genera il CSV da una watchlist ticker tramite provider iniettabile.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_metadata_builder.py`.
- Modulo `src/data/small_cap_metadata_builder.py`.
- Funzione `build_small_cap_metadata`.
- Funzione `write_small_cap_metadata_csv`.
- Provider `yfinance_metadata_provider`.
- Entry point CLI `python -m src.data.small_cap_metadata_builder`.

## Output metadata

```text
symbol
market_cap
is_etf
```

## Diagnostica

Il builder continua anche se un simbolo fallisce e puo' scrivere un CSV diagnostico con:

```text
symbol
status
reason
```

Motivi iniziali:

```text
provider_failed:<errore>
missing_market_cap
missing_is_etf
invalid_market_cap
```

## CLI

Esempio:

```powershell
.\.venv-lab\Scripts\python.exe -m src.data.small_cap_metadata_builder `
  --symbols RKLB,IONQ,SOFI,HOOD,PLTR `
  --output-path data/small_cap_metadata.csv `
  --diagnostics-path data/small_cap_metadata_diagnostics.csv
```

## Testabilita'

I test usano provider fake per evitare rete e rendere il comportamento deterministico. Il provider reale usa `yfinance.Ticker` per `marketCap` e `quoteType`.

## Nota metodologica

Il CSV generato e' un input di ricerca, non una validazione definitiva del float, della liquidita' o della tradabilita'. I filtri operativi restano nel universe builder, nel data-quality report e nell'execution planner.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_metadata_builder.py
4 passed
```

## Prossima mossa

Generare un metadata CSV da una watchlist controllata e usarlo con `src.experiments.small_cap_experiment_cli` per il primo run storico reale.

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-experiment-cli]], [[Roadmap-Master]].
