# Report - Approved Single Provider Sensitivity Diagnostic - 2026-05-18

## Status

```text
APPROVED_SINGLE_DIAGNOSTIC_COMPLETED
PROVIDER_QUERY_PERFORMED
NO_RAW_PAYLOAD_RETENTION
NO_BACKTEST
NO_SWEEP
NO_STRATEGY_PROMOTION
```

## Scope

```text
run_id: RUN-PREREG-PA-SMALLCAP-001-001
preregistration_id: PREREG-PA-SMALLCAP-001
trial_id: TRIAL-001
candidate_count: 1
```

## Candidate result

```text
symbol: CRMD
reference_run: multiyear_2022_2024_risk_sizing
databento_status: pass
databento_rows: 7
polygon_status: OK
polygon_result_count: 1
sensitivity_class: provider_stable_for_selected_fields
return_delta: 0.005296036856533182
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
```

## Safety facts

```text
raw_payload_retained: false
backtest_performed: false
strategy_promotion: false
all_symbols: false
sweep: false
paper/live: false
```

## Interpretation

The single approved diagnostic completed successfully for `CRMD`. Databento and Polygon returned comparable metadata/price fields for this one candidate. The result was classified as `provider_stable_for_selected_fields` for this selected candidate only.

This does not validate the strategy, does not authorize promotion, and does not generalize beyond the single approved diagnostic run.
