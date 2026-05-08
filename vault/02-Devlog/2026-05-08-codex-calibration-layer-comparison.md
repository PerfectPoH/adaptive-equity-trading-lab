---
tipo: devlog
data: 2026-05-08
agente: codex
topic: calibration-layer-comparison
tags: [devlog, calibration, experiments, milestone2]
---

# Sessione Codex - Calibration layer comparison

## Contesto

Dopo il report di calibrazione, il modello raw risultava overconfident. Serviva provare un calibration layer fit solo su validation e capire se migliorava anche i segnali, non solo le metriche statistiche.

## Cosa ho fatto

- Aggiunto `src/models/calibrator.py` con `ProbabilityCalibrator`.
- Il calibratore supporta:
  - `isotonic`;
  - `sigmoid`.
- Il fit usa solo validation rows con label eseguibili.
- Pipeline aggiornata con parametro `calibration_method`.
- Se la run usa calibrazione, `model.joblib` salva il modello probabilistico effettivamente usato.
- Aggiunto `src/experiments/calibration_comparison.py`.
- Dashboard aggiornata con tabella "Latest Calibration Comparison".
- Aggiunto `tests/test_calibrator.py`.

## Risultati

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
```

Output:

```text
experiments/calibration_comparison_latest.json
experiments/calibration_comparison_latest.csv
```

Confronto principale:

```text
raw threshold 0.55:
  strategy return: ~3.21%
  test Brier: ~0.208
  test mean abs calibration error: ~0.212
  signals: 119

isotonic threshold 0.55:
  strategy return: 0.00%
  test Brier: ~0.169
  test mean abs calibration error: ~0.018
  signals: 0

isotonic threshold 0.25:
  strategy return: ~2.00%
  test Brier: ~0.169
  test mean abs calibration error: ~0.018
  signals: 85
```

Verdict:

```text
calibration_improved_probabilities_but_not_strategy
```

## Decisione

La calibrazione migliora nettamente la qualita' probabilistica, ma non migliora ancora la strategia. La soglia calibrata va trattata come una nuova scala, non come equivalente alla soglia raw.

Per ora:

- default operativo: raw probabilities con threshold `0.55`;
- calibrazione: tool di analisi e risk interpretation;
- prossimo step: sweep soglie calibrate piu' ampio o feature-regime analysis.

## Collegamenti

- [[Memoria-AI]]
- [[mvp-core-pipeline]]
- [[Roadmap-Master]]
