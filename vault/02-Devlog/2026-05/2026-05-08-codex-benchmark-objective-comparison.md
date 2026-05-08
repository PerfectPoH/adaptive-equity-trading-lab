---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, benchmark, objective, validation]
---

# 2026-05-08 - Benchmark Objective Comparison

## Contesto

Dopo aver testato ranking, exposure e universe selection, il problema rimasto era chiaro: la strategia fa rendimento positivo ma non batte buy-and-hold. Questa sessione ha testato se cambiare obiettivo del modello potesse aiutare.

## Cosa e' cambiato

- `label_builder.py` ora esporta anche ritorno trade, ritorno benchmark del periodo, excess return e label alternative.
- `walk_forward_validation.py` supporta piu' `ModelObjectiveConfig`.
- Aggiunto runner `src.experiments.benchmark_objective_comparison`.
- Dashboard aggiornata con il report benchmark-objective.
- Docs e vault aggiornati con la decisione.

## Obiettivi confrontati

```text
tp_before_sl
trade_positive
beats_horizon_return
tp_and_beats_horizon
```

## Risultati

```text
wf_2023:
  selected objective: trade_positive
  selected variant: raw
  selected threshold: 0.50
  test strategy return: ~3.06%
  test excess return: ~-98.35%

wf_2024:
  selected objective: tp_before_sl
  selected variant: isotonic
  selected threshold: 0.25
  test strategy return: ~6.49%
  test excess return: ~-41.56%

mean test strategy return: ~4.78%
mean test excess return: ~-69.96%
folds beating buy-and-hold: 0 / 2
```

## Decisione

Non promuovere obiettivi benchmark-aware. Il target `tp_before_sl` resta default.

La cosa importante imparata: il fold 2023 dimostra una trappola da validation. Nel 2022 buy-and-hold era molto negativo, quindi `trade_positive` sembra buono per excess return; nel test 2023, quando il mercato corre, resta drasticamente sotto benchmark.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_labels.py tests\test_walk_forward_validation.py tests\test_calibrator.py
.\.venv-lab\Scripts\python.exe -m src.experiments.benchmark_objective_comparison
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Vedi [[Memoria-AI]], [[Roadmap-Master]], [[backlog]].
