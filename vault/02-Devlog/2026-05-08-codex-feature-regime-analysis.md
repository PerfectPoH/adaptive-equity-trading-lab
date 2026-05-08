---
tipo: devlog
data: 2026-05-08
agente: codex
topic: feature-regime-analysis
tags: [devlog, trade-analysis, regimes, milestone2]
---

# Sessione Codex - Feature regime analysis

## Contesto

Dopo calibration e trade-level analysis, serviva capire se i trade perdenti avevano condizioni comuni al momento del segnale.

## Cosa ho fatto

- Aggiunto `src/analysis/regime_analyzer.py`.
- Aggiunto `tests/test_regime_analyzer.py`.
- Pipeline aggiornata con export:
  - `feature_regime_analysis.csv`
  - `feature_regime_contrasts.csv`
  - `feature_regime_summary.json`
- Dashboard aggiornata con sezione "Feature-Regime Analysis".
- Documentazione aggiornata.

## Verifica

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
```

Risultato:

```text
19 passed
```

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Run generata:

```text
20260508_175742
```

Dashboard:

```text
http://localhost:8501 -> 200
```

## Risultati

Feature-regime summary:

```text
total trades: 36
wins: 23
losses: 13
```

Findings:

```text
Weakest average-return regime:
  signal_distance_from_20d_high = mid
  avg return: ~0.30%
  loss rate: 50%

Highest loss-rate regimes:
  signal_distance_from_20d_high = mid/high
  signal_atr_pct = high
  loss rate: 50%

Largest win/loss contrast:
  losing trades had lower signal_relative_volume_20d than winning trades.
```

## Decisione

Non aggiungere ancora filtri hard: il campione e' piccolo e nessun bucket e' netto negativo.

Ipotesi per prossimo esperimento:

```text
relative_volume_20d > 1.0
avoid distance_from_20d_high mid/high fragility
optional high ATR% guard
```

Ogni filtro va provato come esperimento separato e confrontato con baseline raw `0.55`.

## Collegamenti

- [[Memoria-AI]]
- [[Roadmap-Master]]
- [[Report-Milestone1-2026-05-08]]
