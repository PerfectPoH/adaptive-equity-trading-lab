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
Choose the validation probability variant + threshold with the best excess return,
requiring at least 10 closed validation trades.
Then evaluate only that selected variant/threshold on the next test year.
```

## Latest Result

```text
wf_2023 selected variant: raw
wf_2023 selected feature set: baseline
wf_2023 selected model: random_forest
wf_2023 selected threshold: 0.50
wf_2023 test strategy return: ~5.53%
wf_2023 test excess return: ~-95.88%

wf_2024 selected variant: isotonic
wf_2024 selected feature set: baseline
wf_2024 selected model: random_forest
wf_2024 selected threshold: 0.25
wf_2024 test strategy return: ~6.99%
wf_2024 test excess return: ~-41.06%

mean test strategy return: ~6.26%
mean test excess return: ~-68.47%
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
The calibrated 0.25 variant was selected on 2023 validation and improved the 2024 test result
from ~4.80% raw to ~6.99% without using 2024 to choose the variant.
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

The next improvement should target feature/model quality or the label definition, not just threshold tuning.
