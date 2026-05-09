---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: temporal-embargo
tags: [devlog, embargo, anti-lookahead, validation, milestone2]
---

# 2026-05-09 - Temporal Embargo

## Contesto

Dopo la nota [[Quant-Research-Priorities-2026-05-09]], il prossimo hardening a basso rischio era aggiungere un embargo esplicito ai temporal split. Il progetto aveva gia' purging sulle label forward; mancava un buffer configurabile tra periodi temporali.

## Cosa e' cambiato

- `temporal_split()` in `src/models/trainer.py` accetta `embargo_days` opzionale.
- `build_annual_walk_forward_folds()` in `src/experiments/walk_forward_validation.py` accetta `embargo_days` opzionale.
- Default mantenuto a `0`, quindi nessun default strategico cambia.
- Aggiunti test per:
  - embargo dopo confine train/validation e validation/test;
  - embargo nei fold annuali walk-forward;
  - mantenimento comportamento default senza embargo.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_pipeline_no_lookahead.py tests\test_walk_forward_validation.py
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
```

Risultati:

```text
targeted tests: 20 passed
full suite: 57 passed
walk-forward folds: 2
mean_test_strategy_return: ~5.01%
mean_test_excess_return: ~-69.72%
folds_beating_buy_and_hold: 0
verdict: positive_but_under_benchmark
```

## Decisione

Embargo disponibile ma non attivato nel default. Per attivarlo in futuri esperimenti, passare `embargo_days > 0` al builder dei fold o allo split temporale.

Prossima mossa consigliata: notebook `04_backtest_analysis.ipynb` oppure specifica preliminare cross-sectional, senza altri sweep casuali sulla baseline.

Vedi [[Roadmap-Master]], [[backlog]], [[Regole-Quant]].
