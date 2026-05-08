# Calibration And Trade Analysis

The pipeline now exports model calibration and closed-trade diagnostics for each run.

## Outputs

```text
experiments/runs/<run_id>/calibration.csv
experiments/runs/<run_id>/calibration_summary.json
experiments/runs/<run_id>/trades.csv
experiments/runs/<run_id>/trade_analysis_by_symbol.csv
experiments/runs/<run_id>/trade_analysis_summary.json
```

## Current Default Run

Run:

```text
20260508_175115
```

Signal config:

```text
use_news = false
model_probability_threshold = 0.55
```

Trade summary:

```text
closed trades: 36
wins: 23
losses: 13
trade win rate: ~63.9%
avg trade return: ~3.08%
positive symbols: 8
negative symbols: 1
```

Worst trade:

```text
NVDA
signal date: 2024-06-12
entry date: 2024-06-13
exit date: 2024-06-24
return: ~-6.89%
```

Best trade:

```text
NVDA
signal date: 2024-02-22
entry date: 2024-02-23
exit date: 2024-03-07
return: ~12.79%
```

## Calibration Finding

The model is not well calibrated. Several bins have average predicted probabilities much higher than observed success rates, especially in validation.

Example from validation:

```text
predicted 0.60-0.70 -> observed success ~25.3%
predicted 0.70-0.80 -> observed success 0.0% on a tiny sample
```

This means `model_probability > 0.55` should be treated as a ranking/filter score, not a literal probability of success.

## Calibration Layer Experiment

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
```

Latest comparison:

```text
raw threshold 0.55:
  strategy return: ~3.21%
  test Brier: ~0.208
  test mean abs calibration error: ~0.212
  signals: 119

isotonic calibrated threshold 0.55:
  strategy return: 0.00%
  test Brier: ~0.169
  test mean abs calibration error: ~0.018
  signals: 0

isotonic calibrated threshold 0.25:
  strategy return: ~2.00%
  test Brier: ~0.169
  test mean abs calibration error: ~0.018
  signals: 85
```

Decision:

```text
Calibration improves probability quality, but does not improve the current strategy return.
Keep raw probabilities as the default signal filter for now.
Use calibrated probabilities for risk interpretation and future threshold research.
```

Important detail: validation calibration metrics for isotonic are in-sample for the calibrator. The test calibration metrics are the meaningful out-of-sample check.

## Next Steps

- Run a broader calibrated-threshold sweep before changing the default.
- Run trade-level error analysis by feature regime.
- Investigate AMD losses and NVDA tail risk.
