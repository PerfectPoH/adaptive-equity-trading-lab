# Report - Provider Sensitivity Micro-Check Result - 2026-05-18

## Status

```text
PROVIDER_SENSITIVITY_MICRO_CHECK_EXECUTED
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Scope

This check compares a tiny deterministic sample of old yfinance-era executed trades against Databento Historical OHLCV and Polygon ticker reference evidence.

It is a provider-sensitivity check only. It is not a new strategy trial and does not evaluate whether the strategy works.

## Results

```text
candidates_checked: 4
databento_pass: 3
databento_unavailable_or_error: 1
polygon_reference_pass: 4
provider_stable_for_selected_fields: 1
minor_price_or_return_delta: 2
material_price_or_return_delta: 0
provider_unavailable: 1
raw_response_retention: disabled
```

## Interpretation

Three selected candidates were comparable between old yfinance trade prices and Databento daily OHLCV. None showed a material price/return delta above the pre-declared 5% threshold.

One selected candidate, `CABA` in 2022, was unavailable from Databento/EQUS.MINI in this check. This is consistent with the known Databento EQUS.MINI coverage start being later than that trade window. It is a provider coverage caveat, not evidence about strategy quality.

Polygon ticker reference returned one result for all four selected symbols.

## Verdict

```text
PROVIDER_SENSITIVITY_MICRO_CHECK_CAVEATED
OLD_YFINANCE_RESULTS_NOT_PROVEN_STABLE
OLD_YFINANCE_RESULTS_NOT_PROVEN_INVALID_BY_THIS_MICRO_CHECK
STRATEGY_PROMOTION_REMAINS_BLOCKED
```

## Allowed conclusion

```text
For this tiny sample, comparable Databento rows did not show material price/return deltas, but Databento coverage does not span all old yfinance trade windows. Broader provider-sensitivity conclusions require a pre-registered larger sample and coverage-aware date filtering.
```

## Blocked conclusion

```text
The old strategy works.
The old strategy is provider-stable.
The old strategy can be backtested or paper traded.
```
