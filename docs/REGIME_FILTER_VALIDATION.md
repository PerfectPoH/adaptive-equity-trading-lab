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

This report was generated before timeout-consistent backtesting was added. The qualitative decision still stands, but the numeric baseline has since moved to ~6.49%.

```text
baseline strategy return:          ~6.99% in the previous backtest semantics
volume_floor strategy return:      ~5.09%
pullback_depth strategy return:    ~5.21%
atr_guard strategy return:         ~5.84%
combined_filters strategy return:  ~3.36%
```

Verdict:

```text
filters_did_not_help
```

## Interpretation

The feature-regime analysis produced reasonable hypotheses, but those hypotheses did not survive direct validation as hard filters.

No return filter is good enough to promote. `combined_filters` is the only interesting risk candidate:

```text
baseline max DD:         ~-4.36%
combined_filters max DD: ~-2.92%
```

However, combined filters reduced strategy return materially in that validation, so they should not replace the default without a fresh walk-forward rerun.

## Decision

Keep the default:

```text
use_news = false
isotonic calibrated probabilities
model_probability > 0.25
no regime filters
```

The filter conclusion still stands conceptually: do not add regime filters to the default until they pass their own walk-forward test.

Future work may add combined filters as an optional conservative/risk-first mode, but only after dedicated walk-forward validation.
