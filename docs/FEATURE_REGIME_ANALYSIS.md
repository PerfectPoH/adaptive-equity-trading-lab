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
20260508_181139
```

Primary findings:

```text
Weakest average-return regime:
  signal_distance_from_20d_high = mid
  avg return: ~0.30%
  loss rate: 50%
  trades: 12

Highest loss-rate regimes:
  signal_distance_from_20d_high = mid/high
  signal_atr_pct = high
  loss rate: 50%

Largest win/loss contrast:
  losing trades had lower relative volume than winning trades.
```

Interpretation:

```text
No feature bucket is net negative yet, so there is not enough evidence to add a hard filter.
The strongest hypothesis is that low relative volume and weaker distance-from-high regimes make setups more fragile.
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

None of the tested filters improved strategy return versus the raw baseline:

```text
baseline:          ~3.21%
volume_floor:      ~2.33%
pullback_depth:    ~2.27%
atr_guard:         ~2.85%
combined_filters:  ~1.17%
```

`atr_guard` improved Sharpe and drawdown, but gave up return. It can be revisited as a risk-first mode later, not as the default.
