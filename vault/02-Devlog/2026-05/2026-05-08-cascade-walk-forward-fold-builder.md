---
tipo: devlog
data: 2026-05-08
agente: cascade
topic: walk-forward-fold-builder
tags: [devlog, walk-forward, timeseries-split, milestone2]
---

# 2026-05-08 - Walk-Forward Fold Builder

## Contesto

Dopo model registry e soglie versionate, la prossima voce sicura della Milestone 2 era rendere i fold walk-forward generabili e riusabili invece che hardcoded. L'obiettivo era infrastruttura di validazione, non cambio strategia.

## Cosa e' cambiato

- Aggiunto `build_annual_walk_forward_folds()` in `src/experiments/walk_forward_validation.py`.
- `FOLDS` ora viene generato da:

```text
build_annual_walk_forward_folds(first_validation_year=2022, last_test_year=2024)
```

- I fold restano equivalenti a prima:
  - `wf_2023`: train fino a 2021, validation 2022, test 2023;
  - `wf_2024`: train fino a 2022, validation 2023, test 2024.
- Aggiunto test per verificare finestre expanding train e date dei fold.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_walk_forward_validation.py
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
```

Risultati:

```text
walk-forward tests: 14 passed
full suite: 52 passed
walk-forward summary: positive_but_under_benchmark
folds: 2
mean_test_strategy_return: ~5.01%
mean_test_excess_return: ~-69.72%
folds_beating_buy_and_hold: 0
```

## Decisione

La generazione fold annuali e' pronta per riuso futuro. Non cambia il default strategico e non aggiunge nuovi anni artificialmente. Aggiungere piu' fold resta vincolato ad avere piu' anni/dati migliori.

Prossima mossa sensata: tuning iperparametri su validation, oppure notebook `04_backtest_analysis.ipynb`.

Vedi [[Roadmap-Master]], [[Memoria-AI]], [[Regole-Quant]].
