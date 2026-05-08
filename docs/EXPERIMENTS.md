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

Current best raw variant on the 2024 test-window sweep:

```text
use_news=False
model_probability_threshold=0.50
```

This produced the best 2024 strategy return in a direct test-window sweep, but it is not promoted to default because selecting it would use test information. The default threshold is chosen by walk-forward validation instead.

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
calibration_helped
```

Isotonic calibration improved test Brier score and calibration error. With a retuned threshold of `0.25`, the calibrated strategy improved the 2024 return versus the raw baseline. After adding timeout-consistent backtesting and finalizing end-of-window trades, the default 2024 run is ~6.49%. This is the default research configuration, but it still underperforms buy-and-hold.

## Walk-Forward Validation

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
```

Outputs:

```text
experiments/walk_forward_validation_latest.json
experiments/walk_forward_validation_latest.csv
```

Current verdict:

```text
positive_but_under_benchmark
```

Fold results:

```text
wf_2023:
  validation: 2022
  selected variant: raw
  selected threshold: 0.50
  test year: 2023
  test strategy return: ~3.48%
  test excess return: ~-97.94%

wf_2024:
  validation: 2023
  selected variant: isotonic
  selected threshold: 0.25
  test year: 2024
  test strategy return: ~6.49%
  test excess return: ~-41.56%
```

Decision:

```text
Promote default research configuration to isotonic calibration with model_probability threshold 0.25.
Do not promote raw 0.50 even though it is better in a direct raw-only 2024 sweep, because that is test-window selection.
```

## Model Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.model_comparison
```

Outputs:

```text
experiments/model_comparison_latest.json
experiments/model_comparison_latest.csv
```

Compared models:

```text
logistic_regression
random_forest
hist_gradient_boosting
```

Selection rule:

```text
Choose feature set + model + probability variant + threshold on validation,
requiring at least 30 closed validation trades.
Then evaluate only that selected combination on the next test year.
```

Latest result:

```text
wf_2023 selected: default exit + baseline random_forest raw threshold 0.45
wf_2023 test strategy return: ~6.50%

wf_2024 selected: default exit + baseline random_forest isotonic threshold 0.25
wf_2024 test strategy return: ~6.49%

mean test strategy return: ~6.50%
folds beating buy-and-hold: 0 / 2
```

Decision:

```text
Keep random_forest as the default model.
Do not promote hist_gradient_boosting yet; it did not win under the 30-trade validation floor.
```

## Feature Set Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.feature_set_comparison
```

Outputs:

```text
experiments/feature_set_comparison_latest.json
experiments/feature_set_comparison_latest.csv
```

Compared feature sets:

```text
baseline
enhanced_context
```

Enhanced context adds longer momentum, EMA slopes, intraday range, close position in the 20-day range, volume z-score, dollar-volume context, and SPY context features. These columns are computed by the feature pipeline but are not part of the default training set.

Latest result:

```text
wf_2023 selected: baseline raw threshold 0.45
wf_2023 test strategy return: ~6.50%

wf_2024 selected: baseline isotonic threshold 0.25
wf_2024 test strategy return: ~6.49%

mean test strategy return: ~6.50%
folds beating buy-and-hold: 0 / 2
```

Decision:

```text
Do not promote enhanced_context.
After timeout-consistent backtesting, baseline remains selected in both folds.
```

## Target/Exit Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.target_exit_comparison
```

Outputs:

```text
experiments/target_exit_comparison_latest.json
experiments/target_exit_comparison_latest.csv
```

Compared target/exit configurations:

```text
default_1_5x_stop_3x_tp_10d
fast_1x_stop_2x_tp_5d
balanced_1_5x_stop_2_25x_tp_10d
patient_2x_stop_4x_tp_15d
```

Latest result:

```text
wf_2023 selected: default_1_5x_stop_3x_tp_10d raw threshold 0.45
wf_2023 test strategy return: ~6.50%

wf_2024 selected: balanced_1_5x_stop_2_25x_tp_10d isotonic threshold 0.35
wf_2024 test strategy return: ~6.36%

mean test strategy return: ~6.43%
folds beating buy-and-hold: 0 / 2
```

Decision:

```text
Do not promote the balanced exit config yet.
It is selected on validation for the 2024 fold, but its 2024 test return is slightly worse than the default 2024 run.
```

## Signal Quality Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.signal_quality_comparison
```

Outputs:

```text
experiments/signal_quality_comparison_latest.json
experiments/signal_quality_comparison_latest.csv
```

Compared signal-quality configurations:

```text
no_quality_rank_filter
top_3_daily_quality_score
top_2_daily_quality_score
top_1_daily_quality_score
top_2_daily_model_probability
top_2_daily_scanner_score
top_2_daily_quality_0_50
```

Latest result:

```text
wf_2023 selected: top_2_daily_scanner_score raw threshold 0.45
wf_2023 test strategy return: ~3.36%

wf_2024 selected: no_quality_rank_filter isotonic threshold 0.25
wf_2024 test strategy return: ~6.49%

mean test strategy return: ~4.93%
folds beating buy-and-hold: 0 / 2
```

Decision:

```text
Do not promote a daily rank filter yet.
The ranking filters helped the 2022 validation fold by reducing exposure, but they underperformed badly in the 2023 test year.
For the 2024 fold, validation selected the default no-rank configuration.
Keep signal_quality_score and signal_rank columns as diagnostics only.
```

## Market Exposure Comparison

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.market_exposure_comparison
```

Outputs:

```text
experiments/market_exposure_comparison_latest.json
experiments/market_exposure_comparison_latest.csv
```

Compared market-exposure configurations:

```text
default_1pct
fixed_1_5pct
fixed_2pct
strong_market_1_5pct
strong_market_2pct
weak_0_5pct_strong_1_5pct
```

Latest result:

```text
wf_2023 selected: default_1pct raw threshold 0.45
wf_2023 test strategy return: ~6.50%

wf_2024 selected: fixed_2pct isotonic threshold 0.25
wf_2024 test strategy return: ~11.27%

mean test strategy return: ~8.89%
folds beating buy-and-hold: 0 / 2
```

Decision:

```text
Do not promote higher exposure yet.
The 2024 improvement mostly comes from doubling risk to 2%, not from a better signal edge.
The 2022 validation fold still selected the default 1% risk, and no exposure config beat buy-and-hold out-of-sample.
Keep market exposure configs as research tools until risk-adjusted validation improves.
```

## Feature-Regime Analysis

Current default run:

```text
20260508_200621
```

Current finding:

```text
No feature regime is stable enough for a hard filter yet.
The current calibrated run shows weak buckets around mid signal_quality_score, high distance-from-20d-high, high relative volume, and low calibrated model probability.
```

Decision:

```text
Do not add a hard filter yet. Test relative-volume and distance-from-high filters as a separate logged experiment first.
```

## Regime Filter Validation

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
```

Outputs:

```text
experiments/regime_filter_validation_latest.json
experiments/regime_filter_validation_latest.csv
```

Current verdict:

```text
filters_did_not_help
```

Latest variants:

Note: this regime-filter report was generated before timeout-consistent backtesting. The current default run is ~6.49%; rerun this experiment before promoting any filter.

```text
baseline:
  strategy return: ~6.99% in the previous backtest semantics
  signals: 1093
  closed trades: 140

volume_floor:
  strategy return: ~5.09%
  signals: 441

pullback_depth:
  strategy return: ~5.21%
  signals: 284

atr_guard:
  strategy return: ~5.84%
  Sharpe: below baseline
  negative symbols: 0

combined_filters:
  strategy return: ~3.36%
  signals: 102
```

Decision:

```text
Keep calibrated baseline as default. The filters reduce opportunity too much.
Combined filters improve max drawdown, but sacrifice too much return for the main strategy.
```
