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
