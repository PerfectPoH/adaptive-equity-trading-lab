# Report - Provider Sensitivity Coverage-Aware Expansion - 2026-05-18

## Status

```text
COVERAGE_AWARE_PROVIDER_SENSITIVITY_MICRO_CHECK_EXECUTED
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Scope

The prior micro-check found one Databento-unavailable 2022 case. This expansion filters the old yfinance trade candidates to the Databento/EQUS.MINI coverage window and checks a deterministic sample of up to 8 old trades.

Polygon reference was skipped in this expansion to avoid unnecessary free-plan calls; the objective was Databento-vs-yfinance OHLCV sensitivity inside the covered date range.

## Results

```text
candidates_checked: 8
databento_pass: 8
databento_unavailable_or_error: 0
provider_stable_for_selected_fields: 2
minor_price_or_return_delta: 3
material_price_or_return_delta: 2
provider_unavailable: 0
raw_response_retention: disabled
```

## Interpretation

After filtering to the Databento coverage window, Databento returned all selected OHLCV windows. However, 2 of 8 selected old yfinance trades produced material price/return deltas above the pre-declared 5% threshold.

This is enough to classify the old yfinance-era results as provider-sensitive on the coverage-aware sample.

## Verdict

```text
OLD_YFINANCE_RESULTS_PROVIDER_SENSITIVE_ON_COVERAGE_AWARE_SAMPLE
OLD_STRATEGY_RESULTS_REQUIRE_PROVIDER_SENSITIVITY_WARNING
STRATEGY_PROMOTION_REMAINS_BLOCKED
```

## Allowed conclusion

```text
The old yfinance-era results are not safe to interpret without provider-sensitivity caveats. Databento-comparable rows can differ enough to change per-trade return interpretation in selected cases.
```

## Blocked conclusion

```text
The strategy works.
The strategy fails.
Databento proves/disproves the old backtest.
The setup is ready for paper trading.
```

## Next safe step

```text
ARCHIVE_OLD_STRATEGY_RESULTS_AS_PROVIDER_SENSITIVE
```

Any future strategy work must be a new research track with a provider-aware data foundation, not a continuation of the old yfinance result as if it were stable.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
