---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: implementata-mvp
ultimo-aggiornamento: 2026-05-08
tags: [mvp, pipeline, backtest, ml]
---

# Feature - MVP Core Pipeline

## Obiettivo

Implementare la prima pipeline completa del trading lab senza scope creep.

## Input

- 10 ticker USA;
- daily OHLCV;
- periodo 2020+;
- benchmark buy-and-hold per ticker.

## Output

- snapshot con hash;
- feature;
- label;
- split temporale purgato;
- modello baseline;
- calibrazione validation-only;
- segnali;
- backtest;
- experiment log;
- dashboard.

## Regole chiave

- Entry al next open.
- Split temporale purgato.
- No lookahead.
- No tuning su test.
- Fallimenti documentati.

## Stato

Implementato in prima versione. Il default corrente usa isotonic calibration con soglia 0.25 e produce circa 6.99% medio nel 2024 contro circa 48% buy-and-hold. Non batte il benchmark, quindi la prossima fase deve concentrarsi su feature/model upgrade e validazione, non su live trading.

## File principali

```text
src/pipeline.py
src/data/downloader.py
src/features/feature_pipeline.py
src/models/label_builder.py
src/models/trainer.py
src/strategy/signal_engine.py
src/backtest/runner.py
dashboard/app.py
tests/test_pipeline_no_lookahead.py
```

Vedi [[Report-Milestone1-2026-05-08]].
