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
20260508_174122
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

## Next Steps

- Add probability calibration with validation-only fitting.
- Compare raw Random Forest probabilities vs calibrated probabilities.
- Run trade-level error analysis by feature regime.
- Investigate AMD losses and NVDA tail risk.
