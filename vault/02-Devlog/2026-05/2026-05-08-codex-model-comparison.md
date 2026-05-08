---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, model-comparison, walk-forward, ml]
---

# Devlog - Model Comparison

## Contesto

Dopo aver promosso isotonic `0.25`, il prossimo miglioramento sensato era verificare se il problema fosse il modello baseline. L'obiettivo non era trovare il modello piu' bello sul test, ma scegliere modello, calibrazione e soglia usando solo validation nel walk-forward.

## Cosa e' cambiato

- Aggiunto `hist_gradient_boosting` a `src/models/trainer.py`.
- `run_milestone_1` ora accetta `model_type` e lo salva nei parametri del run.
- `src.experiments.walk_forward_validation` puo' confrontare piu' modelli.
- Aggiunto `src.experiments.model_comparison`.
- Dashboard aggiornata con sezione `Latest Model Comparison`.

## Esperimento

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.model_comparison
```

Modelli:

```text
logistic_regression
random_forest
hist_gradient_boosting
```

Regola:

```text
Scegliere model_type + probability_variant + threshold su validation,
con minimo 30 trade chiusi in validation.
Poi valutare solo la configurazione selezionata sul test successivo.
```

## Risultati

```text
wf_2023:
  selected model: random_forest
  selected variant: raw
  selected threshold: 0.45
  test strategy return: ~7.64%

wf_2024:
  selected model: random_forest
  selected variant: isotonic
  selected threshold: 0.25
  test strategy return: ~6.99%

mean test strategy return: ~7.32%
mean excess return: ~-67.41%
folds beating buy-and-hold: 0/2
```

## Decisione

Random Forest resta il modello default. HistGradientBoosting non viene promosso perche' non vince con il vincolo minimo di 30 trade validation.

Il prossimo miglioramento deve essere sulle feature o sul target, non sul cambio modello a caso.

Vedi [[Memoria-AI]], [[Roadmap-Master]], [[Regole-Quant]].
