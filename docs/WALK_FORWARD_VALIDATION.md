# Walk-Forward Validation

Walk-forward validation is now the source of truth for selecting the default probability threshold.

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
```

Outputs:

```text
experiments/walk_forward_validation_latest.json
experiments/walk_forward_validation_latest.csv
```

## Fold Design

```text
Fold wf_2023:
  train:      <= 2021-12-31
  validation: 2022
  test:       2023

Fold wf_2024:
  train:      <= 2022-12-31
  validation: 2023
  test:       2024
```

Candidate thresholds:

```text
raw:      0.45, 0.50, 0.55, 0.60, 0.65, 0.70
isotonic: 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45
```

Selection rule:

```text
Choose the validation target/exit + feature set + model + probability variant + threshold with the best excess return,
requiring at least 10 closed validation trades.
Then evaluate only that selected combination on the next test year.
```

## Latest Result

```text
wf_2023 selected variant: raw
wf_2023 selected target/exit: default_1_5x_stop_3x_tp_10d
wf_2023 selected feature set: baseline
wf_2023 selected model: random_forest
wf_2023 selected threshold: 0.50
wf_2023 test strategy return: ~3.48%
wf_2023 test excess return: ~-97.94%

wf_2024 selected variant: isotonic
wf_2024 selected target/exit: default_1_5x_stop_3x_tp_10d
wf_2024 selected feature set: baseline
wf_2024 selected model: random_forest
wf_2024 selected threshold: 0.25
wf_2024 test strategy return: ~6.49%
wf_2024 test excess return: ~-41.56%

mean test strategy return: ~5.01%
mean test excess return: ~-69.72%
folds beating buy-and-hold: 0 / 2
```

Verdict:

```text
positive_but_under_benchmark
```

## Decision

Promote the default from:

```text
raw model_probability > 0.45
```

to:

```text
isotonic calibrated model_probability > 0.25
```

Reason:

```text
The calibrated 0.25 variant was selected on 2023 validation. After timeout-consistent backtesting
and finalizing open end-of-window trades, the 2024 default run is ~6.49%.
```

Important caution:

```text
The system still does not beat buy-and-hold in either walk-forward test fold.
This is a research default, not evidence for live capital.
```

## Interpretation

The algorithm improved, but the main weakness remains:

```text
The strategy captures positive returns, but it still underperforms strong buy-and-hold years.
```

Signal ranking, market-exposure/risk fraction configs, and universe selection have now been tested separately and are not promoted yet.
The next improvement should target model edge, broader data coverage, or a stronger benchmark-aware objective rather than simply filtering the current signals.
