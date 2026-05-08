# Regime Filter Validation

This experiment tests whether the patterns found in feature-regime analysis should become actual signal filters.

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
```

Outputs:

```text
experiments/regime_filter_validation_latest.json
experiments/regime_filter_validation_latest.csv
```

## Tested Filters

Baseline:

```text
No regime filters.
```

Volume floor:

```text
relative_volume_20d >= 1.0
```

Pullback depth:

```text
distance_from_20d_high <= -0.021
```

ATR guard:

```text
atr_pct <= 0.0315
```

Combined:

```text
relative_volume_20d >= 1.0
distance_from_20d_high <= -0.021
atr_pct <= 0.0315
```

## Latest Result

```text
baseline strategy return:          ~3.21%
volume_floor strategy return:      ~2.33%
pullback_depth strategy return:    ~2.27%
atr_guard strategy return:         ~2.85%
combined_filters strategy return:  ~1.17%
```

Verdict:

```text
filters_did_not_help
```

## Interpretation

The feature-regime analysis produced reasonable hypotheses, but those hypotheses did not survive direct validation as hard filters.

`atr_guard` is the only interesting candidate:

```text
baseline Sharpe:  ~1.07
atr_guard Sharpe: ~1.37
baseline max DD:  ~-1.48%
atr_guard max DD: ~-1.04%
```

However, `atr_guard` still reduces strategy return from ~3.21% to ~2.85%, so it should not replace the default.

## Decision

Keep the default:

```text
use_news = false
raw probabilities
model_probability > 0.55
no regime filters
```

Future work may add `atr_guard` as an optional conservative/risk-first mode, but not before walk-forward validation.
