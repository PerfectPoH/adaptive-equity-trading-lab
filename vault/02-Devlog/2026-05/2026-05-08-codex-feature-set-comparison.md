---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, feature-set, walk-forward, ml]
---

# Devlog - Feature Set Comparison

## Contesto

Dopo il model comparison, Random Forest e' rimasto il default. Il passo successivo era verificare se il problema fosse la qualita' delle feature, non il modello.

## Cosa e' cambiato

- Aggiunte feature enhanced point-in-time:
  - `rolling_return_10d`;
  - `rolling_return_20d`;
  - `ema_20_slope_5d`;
  - `ema_50_slope_5d`;
  - `intraday_range_pct`;
  - `close_position_20d_range`;
  - `volume_zscore_20d`;
  - `log_avg_dollar_volume_20d`;
  - `spy_return_5d`;
  - `spy_ema_50_ratio`;
  - `spy_rolling_volatility_20d`.
- `FEATURE_COLUMNS` resta baseline.
- `ENHANCED_FEATURE_COLUMNS` e' disponibile solo per esperimenti.
- `src.experiments.walk_forward_validation` supporta confronto tra feature set.
- Aggiunto `src.experiments.feature_set_comparison`.
- Dashboard aggiornata con `Latest Feature Set Comparison`.

## Esperimento

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.feature_set_comparison
```

Feature set:

```text
baseline
enhanced_context
```

Regola:

```text
Scegliere feature_set + model_type + probability_variant + threshold su validation,
con minimo 30 trade chiusi in validation.
Poi valutare solo la configurazione selezionata sul test successivo.
```

## Risultati

```text
wf_2023:
  selected feature set: baseline
  selected variant: raw
  selected threshold: 0.45
  test strategy return: ~7.64%

wf_2024:
  selected feature set: enhanced_context
  selected variant: isotonic
  selected threshold: 0.20
  test strategy return: ~6.60%

mean test strategy return: ~7.12%
mean excess return: ~-67.61%
folds beating buy-and-hold: 0/2
```

## Decisione

Non promuovere `enhanced_context`. Anche se viene scelto sulla validation 2023 per il fold 2024, sul test 2024 peggiora il risultato rispetto al baseline default (~6.60% contro ~6.99%).

La prossima direzione non e' aggiungere feature tecniche a blocchi, ma lavorare su target, universo, ranking, o criteri di uscita.

Vedi [[Memoria-AI]], [[Roadmap-Master]], [[Regole-Quant]].
