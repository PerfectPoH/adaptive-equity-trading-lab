---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: backtest-analysis
tags: [devlog, backtest, analysis, milestone2]
---

# 2026-05-09 - Backtest Analysis

## Contesto

Dopo embargo e research-priorities, il prossimo task Milestone 2 era `04_backtest_analysis.ipynb`: analizzare perche' la baseline resta sotto buy-and-hold prima di cambiare paradigma o aggiungere altri sweep.

## Cosa e' cambiato

- Aggiunto modulo testabile `src/analysis/backtest_report.py`.
- Aggiunto runner `src/analysis/backtest_report_runner.py`.
- Aggiunto notebook `notebooks/04_backtest_analysis.ipynb` come entrypoint riproducibile.
- Generato report `experiments/backtest_analysis_latest.md` dal latest run disponibile.

## Risultato report

Run analizzato:

```text
20260508_212205
```

Verdict:

```text
underperforming_buy_and_hold
```

Metriche aggregate:

```text
strategy_return: ~6.49%
buy_and_hold_return: ~48.05%
excess_return: ~-41.56%
total_trades: 193
win_rate: ~54.40%
```

Peggiori simboli per excess return:

```text
NVDA: ~-165.12%
META: ~-60.43%
TSLA: ~-59.20%
AMZN: ~-36.65%
GOOGL: ~-29.21%
```

Findings regime/feature principali:

```text
Weakest average-return regime: signal_signal_quality_score mid.
Highest loss-rate regime: signal_signal_quality_score mid.
Losing trades had higher signal_relative_volume_20d than winning trades.
```

## Decisione

Non promuovere la strategia. Il report conferma che il problema e' nella selezione/qualita' dei trade rispetto al benchmark, non in una singola soglia o iperparametro.

Prossima mossa consigliata: specifica cross-sectional leggera, focalizzata su ranking relativo e portfolio construction, prima di implementare nuove label.

Vedi [[Roadmap-Master]], [[Quant-Research-Priorities-2026-05-09]], [[2026-05-09-cascade-temporal-embargo]].
