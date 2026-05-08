---
tipo: devlog
data: 2026-05-08
agente: codex
topic: regime-filter-validation
tags: [devlog, experiments, regime-filters, milestone2]
---

# Sessione Codex - Regime filter validation

## Contesto

La feature-regime analysis aveva indicato possibili fragilita':

- volume relativo basso;
- distance-from-20d-high mid/high;
- ATR% alto.

Serviva testare questi pattern come filtri reali senza cambiare il default.

## Cosa ho fatto

- Aggiunti filtri opzionali in `src/strategy/signal_engine.py`:
  - `min_relative_volume`;
  - `max_distance_from_20d_high`;
  - `max_atr_pct`.
- Pipeline aggiornata per passare e loggare `regime_filters`.
- Aggiunto `src/experiments/regime_filter_validation.py`.
- Dashboard aggiornata con "Latest Regime Filter Validation".
- Aggiunto `tests/test_signal_engine.py`.

## Verifica

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
```

Risultato:

```text
21 passed
```

Experiment runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
```

Output:

```text
experiments/regime_filter_validation_latest.json
experiments/regime_filter_validation_latest.csv
```

## Risultati

```text
baseline:
  strategy return: ~3.21%
  signals: 119
  closed trades: 36

volume_floor:
  strategy return: ~2.33%
  signals: 65
  closed trades: 26

pullback_depth:
  strategy return: ~2.27%
  signals: 36
  closed trades: 20

atr_guard:
  strategy return: ~2.85%
  Sharpe: ~1.37
  max drawdown: ~-1.04%
  negative symbols: 0

combined_filters:
  strategy return: ~1.17%
  signals: 13
  closed trades: 9
```

Verdict:

```text
filters_did_not_help
```

## Decisione

Non promuovere nessun filtro a default. I filtri tagliano troppe opportunita' e riducono il rendimento medio.

Nota utile:

```text
atr_guard migliora Sharpe e drawdown, quindi puo' diventare una modalita' risk-first futura.
```

Ma va rivalutato solo dopo walk-forward validation.

## Collegamenti

- [[Memoria-AI]]
- [[Roadmap-Master]]
- [[Report-Milestone1-2026-05-08]]
- [[2026-05-08-codex-feature-regime-analysis]]
