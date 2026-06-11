---
tipo: devlog
data: 2026-05-08
agente: codex
topic: ablation-threshold-validation
tags: [devlog, ablation, threshold, validation]
---

# Sessione Codex - Ablation e threshold validation

## Contesto

Dopo aver collegato GDELT, serviva capire se le news aiutavano davvero e se la soglia `model_probability > 0.60` era troppo restrittiva.

## Cosa ho fatto

- Aggiunto `src.experiments.news_ablation`.
- Aggiunto `src.experiments.threshold_validation`.
- Aggiunto `src/analysis/threshold_analyzer.py`.
- Resa configurabile la pipeline: `use_news`, `min_model_probability`, `min_scanner_score`.
- Dashboard aggiornata con report ablation/threshold.
- Default sperimentale aggiornato a `use_news=false`, `model_probability > 0.55`.

## Risultati news ablation

```text
verdict: mixed_or_inconclusive
strategy_return_delta news-vs-no-news: -0.006657
validation_roc_auc_delta: +0.03754
test_roc_auc_delta: -0.00216
```

Interpretazione: le news migliorano la validation ROC AUC, ma non migliorano il backtest 2024. Restano sperimentali, non default.

## Risultati threshold validation

Miglior setup tra quelli provati:

```text
use_news=false
threshold=0.55
strategy_return ~ 3.21%
buy_and_hold ~ 48.0%
signals: 119
symbols_with_signals: 9
```

Rispetto a threshold `0.60`, `0.55` aumenta molto la copertura e migliora il rendimento, ma resta lontanissimo dal benchmark.

## Prossima sessione consigliata

- Backtest threshold sweep piu' ampio con scelta solo su validation.
- Calibration plot.
- Error analysis trade-level: quali setup perdono e perche'.
- Valutare target/risk-reward diversi, non solo soglia.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
