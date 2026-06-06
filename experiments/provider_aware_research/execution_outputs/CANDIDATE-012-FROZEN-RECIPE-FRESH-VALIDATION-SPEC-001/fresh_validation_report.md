# Candidate 012 Frozen Recipe Fresh Validation Spec

Decision: `CANDIDATE_012_FROZEN_RECIPE_AWAITING_FRESH_DATA`

Candidate 011 is frozen exactly as discovered. No additional backtest is authorized until a separate fresh-data gate is committed.

## Frozen Recipe

- Regime: `RISK_OFF`
- Sleeve: `risk_off_mean_reversion_5d`
- Lookback days: `5`
- Holding days: `10`
- Top K: `20`
- Cost bps round trip: `500`

## Candidate 011 Observation

- OOS trades: `19`
- OOS weighted net: `0.06586794899032468`
- OOS median net: `0.04353333624035231`
- OOS win rate: `0.7368421052631579`

## Fresh Data Requirements

- Minimum history years: `5`
- Must include delisted: `True`
- Forbidden discovery dataset: `experiments/provider_aware_research/data_inputs/CANDIDATE-007-NORGATE-DATASET-RERUN-002`

## Future Validation Gates

- Min OOS trades: `30`
- Positive ex-top3 required: `True`
- Positive ex-top10pct required: `True`
- Must beat SPY/IWM: `True` / `True`

## Blockers

- `fresh_data_gate_required_before_backtest`
- `same_dataset_reuse_forbidden`
- `trial_limited_discovery_not_promotable`
