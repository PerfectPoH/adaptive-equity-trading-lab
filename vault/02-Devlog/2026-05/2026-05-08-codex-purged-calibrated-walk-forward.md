---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, walk-forward, calibration, anti-lookahead, snapshots]
---

# Devlog - Purged Calibrated Walk-Forward

## Contesto

Obiettivo della sessione: migliorare l'algoritmo senza aumentare scope in modo casuale. Durante il controllo e' emerso un rischio metodologico: le label forward venivano costruite sull'intero storico e poi splittate. Questo poteva far usare prezzi oltre il confine train/validation/test nelle ultime barre di ogni periodo.

## Cosa e' cambiato

- Aggiunto `purge_label_boundary` in `src/models/trainer.py`.
- `temporal_split` ora elimina le ultime 10 barre per simbolo da train, validation e test se la label TP-before-SL supererebbe il confine del periodo.
- Walk-forward validation ora usa train purgato.
- Walk-forward validation confronta anche raw probabilities contro isotonic calibration.
- Default di ricerca aggiornato a:

```text
use_news=false
calibration_method=isotonic
model_probability > 0.25
no regime filters
```

- Downloader migliorato: se `yfinance` fallisce o restituisce dati invalidi, prova l'ultimo snapshot locale valido.
- Dashboard chiarita: i threshold diagnostics label-based non sono il default operativo.

## Risultati

Run default:

```text
run_id: 20260508_185027
strategy_return: ~6.99%
buy_and_hold_return: ~48.05%
excess_return: ~-41.06%
signals: 1093
executable signals: 1036
closed trades: 140
trade win rate: ~52.1%
```

Walk-forward:

```text
wf_2023: raw threshold 0.50 -> test 2023 return ~5.53%
wf_2024: isotonic threshold 0.25 -> test 2024 return ~6.99%
mean test return: ~6.26%
folds beating buy-and-hold: 0/2
verdict: positive_but_under_benchmark
```

Regime filters:

```text
baseline: ~6.99%
volume_floor: ~5.09%
pullback_depth: ~5.21%
atr_guard: ~5.84%
combined_filters: ~3.36%
```

Verdict: i filtri non migliorano il rendimento. Combined filters migliorano max drawdown, ma tagliano troppo rendimento.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_downloader.py
.\.venv-lab\Scripts\python.exe -m pytest tests\test_pipeline_no_lookahead.py tests\test_walk_forward_validation.py tests\test_signal_engine.py
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.threshold_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
```

Final full test suite:

```text
26 passed
```

## Decisione

Promuovere isotonic `0.25` come default di ricerca per la prossima iterazione, ma non trattarlo come strategia pronta. Il sistema resta sotto buy-and-hold e va migliorato con feature/model upgrade, non con tuning infinito delle soglie.

Vedi [[Memoria-AI]], [[Roadmap-Master]], [[backlog]].
