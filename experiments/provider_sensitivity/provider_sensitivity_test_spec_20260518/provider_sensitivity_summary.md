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
