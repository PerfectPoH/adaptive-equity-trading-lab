# Experiments

This project keeps small reproducible experiment runners under `src/experiments/`.

## News Ablation

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.news_ablation
```

Outputs:

```text
experiments/news_ablation_latest.json
experiments/news_ablation_latest.csv
```

Current verdict:

```text
mixed_or_inconclusive
```

News improved validation ROC AUC but did not improve the 2024 backtest return.

## Threshold Validation

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.threshold_validation
```

Outputs:

```text
experiments/threshold_validation_latest.json
experiments/threshold_validation_latest.csv
```

Current best variant:

```text
use_news=False
model_probability_threshold=0.55
```

This produced more signals and better 2024 strategy return than the stricter `0.60` threshold, while still underperforming buy-and-hold.

## Calibration And Trade Analysis

Every pipeline run now exports:

```text
calibration.csv
calibration_summary.json
trades.csv
trade_analysis_by_symbol.csv
trade_analysis_summary.json
feature_regime_analysis.csv
feature_regime_contrasts.csv
feature_regime_summary.json
```

Current finding: the raw model is overconfident, so raw probabilities should be treated as ranking scores rather than literal success probabilities.

## Calibration Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
```

Outputs:

```text
experiments/calibration_comparison_latest.json
experiments/calibration_comparison_latest.csv
```

Current verdict:

```text
calibration_improved_probabilities_but_not_strategy
```

Isotonic calibration improved test Brier score and calibration error, but the calibrated probability scale needs a lower threshold. With threshold `0.25`, calibrated signals still underperformed the raw `0.55` baseline, so the default remains raw probabilities for now.

## Feature-Regime Analysis

Current default run:

```text
20260508_175742
```

Current finding:

```text
No feature regime is net negative yet, but the weakest buckets are tied to mid/high distance-from-20d-high regimes, high ATR%, and lower relative volume.
```

Decision:

```text
Do not add a hard filter yet. Test relative-volume and distance-from-high filters as a separate logged experiment first.
```
