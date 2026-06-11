# Report - First Preregistered Provider-Aware Research Plan - 2026-05-18

## Status

```text
FIRST_PROVIDER_AWARE_RESEARCH_PLAN_PREREGISTERED_PRE_RUN_FIELDS_FINALIZED_NOT_RUN
PLAN_ONLY_NOT_EXECUTED
VALIDATOR_UPDATED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Purpose

This artifact finalizes the pre-run fields for the first provider-aware research plan while keeping the plan not executed.

## Finalized pre-run fields

```text
primary_metric: median_next_session_open_to_close_return
hypothesis: provider-aware small-cap opening-gap continuation diagnostic
minimum_gap: 0.10
minimum_price: 2.00
minimum_dollar_volume: 1000000
market_regime_filter: IWM close > EMA200
event_window: next_session_open_to_close
max_trials: 3
```

## Linked governance artifacts

```text
research_run_gate_spec: experiments/provider_aware_research/research_run_gate_spec_20260518
provider_coverage_contract: experiments/provider_aware_research/provider_coverage_contract_spec_20260518
adjustment_tradability_policy: experiments/provider_aware_research/adjustment_tradability_policy_spec_20260518
trial_accounting_preregistration: experiments/provider_aware_research/trial_accounting_preregistration_spec_20260518
```

## Remaining restrictions

```text
execution_status: not_executed
provider_queries: forbidden in this step
backtests: forbidden in this step
parameter sweeps: forbidden
promotion: blocked
PIT_claim: blocked for universe-wide claims
raw_data_retention: derived_only
```

## Validator

```text
validator_module: src/experiments/preregistered_research_plan_validator.py
test_module: tests/test_preregistered_research_plan_validator.py
real_plan_validation: pass
real_plan_checks: 45 passed / 0 failed
research_run_gate_validation: pass for new_signal_research
research_run_gate_checks: 31 passed / 0 failed
pytest_target: preregistered plan + governance validators
pytest_result: 25 passed
```

## Required interpretation

This is still not a strategy result, not a backtest, not an OOS validation, and not evidence of performance. It is only a finalized preregistered plan ready for a separate explicit execution decision.

## Next safe step

```text
CREATE_EXPLICIT_EXECUTION_AUTHORIZATION_ARTIFACT_SPEC_ONLY
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
