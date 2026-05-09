---
tipo: devlog
data: 2026-05-08
agente: cascade
topic: hyperparameter-comparison
tags: [devlog, hyperparameter, validation, milestone2]
---

# 2026-05-08 - Hyperparameter Comparison

## Contesto

Dopo il fold builder walk-forward, la prossima voce Milestone 2 era tuning iperparametri su validation, non su test. L'obiettivo era confrontare configurazioni Random Forest in walk-forward senza cambiare il default operativo.

## Cosa e' cambiato

- `build_model()` e `fit_model()` supportano `model_params` opzionali.
- `run_walk_forward_validation()` supporta `ModelConfig`, distinguendo `model_config` da `model_type`.
- Aggiunto runner `src.experiments.hyperparameter_comparison`.
- La dashboard mostra `Latest Hyperparameter Comparison` se il report CSV esiste.
- Aggiunti test per:
  - override parametri Random Forest;
  - serializzazione `ModelConfig`;
  - selezione validation-only tra `model_config` diverse.

## Configurazioni confrontate

```text
random_forest_default: default corrente
random_forest_shallow: max_depth=4, min_samples_leaf=30
random_forest_deeper: max_depth=8, min_samples_leaf=15
```

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_trainer.py tests\test_walk_forward_validation.py
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.experiments.hyperparameter_comparison
```

Risultati:

```text
trainer + walk-forward tests: 19 passed
full suite: 55 passed
hyperparameter comparison verdict: positive_but_under_benchmark
folds: 2
mean_test_strategy_return: ~6.49%
mean_test_excess_return: ~-68.24%
folds_beating_buy_and_hold: 0
```

## Selezione walk-forward

```text
wf_2023: random_forest_default, raw threshold 0.45 -> test strategy return ~6.50%
wf_2024: random_forest_shallow, isotonic threshold 0.20 -> test strategy return ~6.47%
```

## Decisione

Non promuovere nuovi iperparametri a default. `random_forest_shallow` viene scelto nel fold 2024, ma il risultato out-of-sample resta sotto buy-and-hold e non migliora abbastanza rispetto al default corrente.

Prossima mossa sensata: notebook `04_backtest_analysis.ipynb` oppure analisi piu' profonda dei trade/feature prima di nuove griglie.

Vedi [[Roadmap-Master]], [[Memoria-AI]], [[Regole-Quant]].
