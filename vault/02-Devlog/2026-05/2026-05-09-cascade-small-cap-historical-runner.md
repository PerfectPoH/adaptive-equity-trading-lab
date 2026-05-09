---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-historical-runner
tags: [devlog, small-cap, runner, historical, backtest, tdd]
---

# 2026-05-09 - Small-Cap Historical Runner

## Contesto

Dopo candidate export, benchmark report e backtest/report proxy, serviva un runner end-to-end che producesse artefatti riproducibili per una finestra storica definita.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_historical_runner.py`.
- Modulo `src/experiments/small_cap_historical_runner.py`.
- Config `SmallCapHistoricalRunConfig`.
- Funzione `run_small_cap_historical_report`.

## Input

```text
candidate_metadata
frames
output_dir
iwm_frame opzionale
as_of_dates opzionale
start/end opzionale
SmallCapHistoricalRunConfig
```

## Artefatti prodotti

```text
candidate_export.csv
benchmark_report.csv
small_cap_backtest_report.md
```

## Pipeline

```text
for each as_of date:
  build_small_cap_candidate_export(..., operational_only=False)
concat candidate exports
build_small_cap_benchmark_report(...)
write_small_cap_backtest_report_markdown(...)
```

## Regole date

- Se `as_of_dates` e' esplicito, il runner usa quelle date.
- Se non e' esplicito, il runner deriva le date dagli indici dei frame, escludendo l'ultima barra disponibile per evitare `no_next_open` sistematico.
- `start/end` filtrano le date selezionate.
- Se non ci sono date disponibili, il runner fallisce con `ValueError`.

## Nota metodologica

Il runner produce un esperimento storico riproducibile basato sul report/proxy small-cap. Non e' ancora un portfolio backtest engine completo con gestione di cash, posizioni sovrapposte e order lifecycle multi-simbolo.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_historical_runner.py
3 passed
```

## Prossima mossa

Aggiungere un loader dati reale per small-cap universe e un comando/CLI che costruisca metadata, frames e IWM proxy prima di chiamare il runner.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-candidate-export]], [[2026-05-09-cascade-small-cap-benchmarks]], [[2026-05-09-cascade-small-cap-backtest-report]], [[Roadmap-Master]].
