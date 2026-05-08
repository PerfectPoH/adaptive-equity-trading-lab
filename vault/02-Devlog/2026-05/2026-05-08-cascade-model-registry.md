---
tipo: devlog
data: 2026-05-08
agente: cascade
topic: model-registry
tags: [devlog, model-registry, joblib, milestone2]
---

# 2026-05-08 - Model Registry

## Contesto

Dopo il push iniziale su GitHub, la prossima voce sicura della Milestone 2 era aggiungere un registry dei modelli senza cambiare logica trading, segnali, rischio o soglie.

## Cosa e' cambiato

- Aggiunto `src/models/registry.py`.
- Ogni modello `model.joblib` puo' essere registrato con hash SHA-256, configurazione, periodi train/validation/test e metriche.
- La pipeline ora scrive `experiments/model_registry.csv` e `model_metadata.json` nella cartella della run.
- `summary.json` include `model_metadata_path` e `model_registry_path`.
- La dashboard mostra la tabella `Model Registry` se il CSV esiste.
- Aggiunto `tests/test_model_registry.py`.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_model_registry.py
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Risultati:

```text
test_model_registry: 1 passed
full suite: 49 passed
pipeline run: 20260508_211515
```

## Risultato run

```text
strategy_return: ~6.49%
buy_and_hold_return: ~48.05%
excess_return: ~-41.56%
model_registry: experiments/model_registry.csv
model_sha256: 1c9c17deb6c98b4fd10e342ce9f7866943b8d737b94a14947599af267a45ba95
```

## Decisione

`Model registry con joblib` e' completato come tracciabilita' minima. Non cambia il default strategico e non rende la strategia pronta per capitale reale.

Prossima mossa sensata: versionare soglie scanner/modello oppure creare `04_backtest_analysis.ipynb`.

Vedi [[Roadmap-Master]], [[Memoria-AI]], [[Regole-Quant]].
