---
tipo: devlog
data: 2026-05-08
agente: cascade
topic: threshold-config
tags: [devlog, threshold-config, milestone2]
---

# 2026-05-08 - Threshold Config Versionata

## Contesto

Dopo il model registry, la prossima voce sicura della Milestone 2 era versionare soglie scanner/modello. L'obiettivo era aumentare tracciabilita' senza cambiare strategia, soglie operative o rischio.

## Cosa e' cambiato

- Aggiunto `src/strategy/threshold_config.py`.
- Aggiunta `ThresholdConfig` immutabile con serializzazione `to_dict()`.
- Default versionato:

```text
thresholds_v2026_05_08_isotonic_025
```

- La pipeline ora deriva i default da `DEFAULT_THRESHOLD_CONFIG`:
  - `model_type=random_forest`;
  - `calibration_method=isotonic`;
  - `min_scanner_score=70`;
  - `min_model_probability=0.25`.
- `threshold_config` viene scritto in `summary.json`, `experiments/log.csv`, `model_metadata.json` e `experiments/model_registry.csv`.
- Aggiunto `tests/test_threshold_config.py`.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_threshold_config.py tests\test_model_registry.py
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Risultati:

```text
threshold/model-registry tests: 3 passed
full suite: 51 passed
pipeline run: 20260508_212205
```

## Risultato run

```text
strategy_return: ~6.49%
buy_and_hold_return: ~48.05%
excess_return: ~-41.56%
threshold_version: thresholds_v2026_05_08_isotonic_025
```

## Decisione

Soglie scanner/modello ora sono versionate e tracciate nei log. Questo non promuove nuove soglie e non cambia il default strategico.

Prossima mossa sensata: `TimeSeriesSplit`, tuning iperparametri su validation oppure notebook `04_backtest_analysis.ipynb`.

Vedi [[Roadmap-Master]], [[Memoria-AI]], [[Regole-Quant]].
