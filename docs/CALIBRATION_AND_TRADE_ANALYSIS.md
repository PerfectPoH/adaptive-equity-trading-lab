# Calibration And Trade Analysis

The pipeline now exports model calibration and closed-trade diagnostics for each run.

## Outputs

```text
experiments/runs/<run_id>/calibration.csv
experiments/runs/<run_id>/calibration_summary.json
experiments/runs/<run_id>/trades.csv
experiments/runs/<run_id>/trade_analysis_by_symbol.csv
experiments/runs/<run_id>/trade_analysis_summary.json
experiments/runs/<run_id>/feature_regime_analysis.csv
experiments/runs/<run_id>/feature_regime_contrasts.csv
experiments/runs/<run_id>/feature_regime_summary.json
```

## Current Default Run

Run:

```text
20260508_192713
```

Signal config:

```text
use_news = false
calibration_method = isotonic
model_probability_threshold = 0.25
```

Trade summary:

```text
closed trades: 193
wins: 105
losses: 88
trade win rate: ~54.4%
avg trade return: ~1.13%
positive symbols: 10
negative symbols: 0
```

Worst trade:

```text
TSLA
signal date: 2024-07-12
entry date: 2024-07-15
exit date: 2024-07-24
return: ~-12.12%
```

Best trade:

```text
TSLA
signal date: 2024-11-06
entry date: 2024-11-07
exit date: 2024-11-11
return: ~19.65%
```

## Calibration Finding

The model is not well calibrated. Several bins have average predicted probabilities much higher than observed success rates, especially in validation.

Example from validation:

```text
predicted 0.60-0.70 -> observed success ~25.3%
predicted 0.70-0.80 -> observed success 0.0% on a tiny sample
```

This means raw `model_probability` should be treated as a ranking/filter score, not a literal probability of success. The current default therefore uses an isotonic calibration layer fit on validation only.

## Calibration Layer Experiment

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
```

Latest comparison:

```text
raw threshold 0.45:
  strategy return: ~4.80%
  test Brier: ~0.208
  test mean abs calibration error: ~0.207
  signals: 616

isotonic calibrated threshold 0.45:
  strategy return: 0.00%
  test Brier: ~0.172
  test mean abs calibration error: ~0.042
  signals: 0

isotonic calibrated threshold 0.25:
  strategy return: ~6.49% after timeout-consistent backtesting
  test Brier: ~0.172
  test mean abs calibration error: ~0.042
  signals: 1093
```

Decision:

```text
Calibration improves probability quality and, after threshold retuning, improves strategy return.
Promote isotonic calibration with threshold 0.25 as the current research default.
Still treat this as a prototype: it remains far below buy-and-hold in 2024.
```

Important detail: validation calibration metrics for isotonic are in-sample for the calibrator. The test calibration metrics are the meaningful out-of-sample check.

## Next Steps

- Add a broader calibrated-threshold sweep inside walk-forward.
- Investigate whether the broader calibrated signal set needs separate risk controls.
- Add more years or a better point-in-time dataset before trusting the calibration result.
