# Feature-Regime Analysis

Every pipeline run now exports a feature-regime diagnostic for closed trades.

## Outputs

```text
experiments/runs/<run_id>/feature_regime_analysis.csv
experiments/runs/<run_id>/feature_regime_contrasts.csv
experiments/runs/<run_id>/feature_regime_summary.json
```

## What It Measures

The analyzer groups closed trades into low/mid/high buckets for signal-time features:

```text
model probability
scanner score
ATR percentage
relative volume
distance from 20-day high
20-day rolling volatility
news stress
news tone
```

It then reports:

```text
win rate
loss rate
average return
median return
total PnL
win/loss feature contrasts
```

## Current Default Run

Run:

```text
20260508_185027
```

Primary findings:

```text
Weakest average-return regime:
  signal_rolling_volatility_20d = low
  avg return: ~0.38%
  loss rate: ~53.2%
  trades: 47

Highest loss-rate regimes:
  signal_distance_from_20d_high = high
  signal_model_probability = low
  signal_rolling_volatility_20d = low

Best regimes:
  signal_distance_from_20d_high = mid
  calibrated signal_model_probability = high
  calibrated signal_model_probability = mid

Largest win/loss contrast:
  losing trades had slightly higher relative volume than winning trades.
```

Interpretation:

```text
No feature bucket is net negative yet, so there is not enough evidence to add a hard filter.
The strongest current hypothesis is that setups too close to the 20-day high and low calibrated-probability buckets are more fragile.
```

## Decision

Do not change the strategy yet.

The filter experiment was run:

```text
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
```

Result:

```text
filters_did_not_help
```

None of the tested filters improved strategy return versus the calibrated baseline:

```text
baseline:          ~6.99%
volume_floor:      ~5.09%
pullback_depth:    ~5.21%
atr_guard:         ~5.84%
combined_filters:  ~3.36%
```

No hard filter improved strategy return. Combined filters improved max drawdown, but gave up too much return. Any filter needs its own walk-forward validation before promotion.
