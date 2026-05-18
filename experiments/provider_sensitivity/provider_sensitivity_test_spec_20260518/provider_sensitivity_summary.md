# Provider sensitivity test spec summary

```text
PROVIDER_SENSITIVITY_TEST_SPEC_CREATED
SPEC_ONLY_NOT_EXECUTED
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
```

The proposed test asks whether old yfinance-based strategy outputs are materially sensitive to provider data differences. The test is not authorized to evaluate whether the old strategy works.

Current readiness verdict:

```text
NOT_READY_TO_EXECUTE_PROVIDER_SENSITIVITY_TEST
READY_TO_PREPARE_OVERLAP_SELECTION_AND_QUERY_PLAN
```

Reason: Databento+Polygon provider join is currently approved for metadata/data-quality only, not as a performance dataset. A tiny deterministic overlap set and redacted query plan must be committed before any provider query.

## Preparation update

```text
OVERLAP_SELECTION_PREPARED
REDACTED_QUERY_PLAN_PREPARED
PROVIDER_QUERY_EXECUTED: no
READY_FOR_USER_REVIEW_BEFORE_EXECUTION: yes
READY_TO_EXECUTE_WITHOUT_REVIEW: no
```

Artifacts added:

```text
overlap_selection_candidates.csv
overlap_selection_summary.csv
redacted_query_plan.csv
```

## Micro-check execution update

```text
PROVIDER_SENSITIVITY_MICRO_CHECK_EXECUTED
candidates_checked: 4
databento_pass: 3
databento_unavailable_or_error: 1
polygon_reference_pass: 4
provider_stable_for_selected_fields: 1
minor_price_or_return_delta: 2
provider_unavailable: 1
material_price_or_return_delta: 0
raw_response_retention: disabled
strategy_promotion_allowed: no
```

Interpretation: selected comparable cases do not show material price/return deltas above the pre-declared 5% threshold, but one 2022 CABA case is unavailable from Databento/EQUS.MINI because the product coverage begins later than that trade window. This is a provider-coverage caveat, not strategy evidence.

## Coverage-aware expansion update

```text
COVERAGE_AWARE_PROVIDER_SENSITIVITY_MICRO_CHECK_EXECUTED
candidates_checked: 8
databento_pass: 8
databento_unavailable_or_error: 0
polygon_reference: skipped_for_rate_limit_and_reference_scope
provider_stable_for_selected_fields: 2
minor_price_or_return_delta: 3
material_price_or_return_delta: 2
provider_unavailable: 0
raw_response_retention: disabled
strategy_promotion_allowed: no
```

Interpretation: after filtering to the Databento/EQUS.MINI coverage window, Databento returned all selected windows, but 2/8 selected trades show material price/return deltas above the pre-declared 5% threshold. This is enough to classify old yfinance-era outputs as provider-sensitive on this coverage-aware sample. It is still not strategy evidence and does not authorize backtests or promotion.

## Old signal price replay full coverage update

```text
OLD_SIGNAL_PRICE_REPLAY_FULL_COVERAGE_DIAGNOSTIC_EXECUTED
replay_candidates: 66
databento_pass: 66
databento_unavailable_or_error: 0
provider_stable_for_selected_fields: 25
minor_price_or_return_delta: 35
material_price_or_return_delta: 6
provider_unavailable: 0
max_abs_return_delta: 0.2084676744010346
median_abs_return_delta: 0.0108600878613564
raw_response_retention: disabled
strategy_promotion_allowed: no
```

Verdict: `OLD_SIGNAL_RETURNS_PROVIDER_SENSITIVE_FULL_COVERAGE_REPLAY`. The old yfinance-era signals are replayable on Databento-covered dates, but provider deltas are material in 6/66 rows. This supports archiving old strategy results as provider-sensitive, not running a portfolio backtest.
