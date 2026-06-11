# Report - Research Run Gate Spec - 2026-05-18

## Status

```text
RESEARCH_RUN_GATE_REQUIRED_BEFORE_ANY_PROVIDER_AWARE_RUN
SPEC_ONLY_NOT_EXECUTED
VALIDATOR_IMPLEMENTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Purpose

This gate aggregates required governance validators before any provider-aware research run.

## Required components

```text
provider_coverage_contract
adjustment_tradability_policy
trial_accounting_preregistration
```

## Default decision

```text
BLOCK_UNLESS_ALL_REQUIRED_COMPONENTS_PASS
```

## Stage policy

```text
data_quality_diagnostic: coverage + adjustment/tradability required
fixed_signal_replay: coverage + adjustment/tradability required
new_signal_research: coverage + adjustment/tradability + preregistration required
portfolio_backtest: coverage + adjustment/tradability + preregistration required
OOS: coverage + adjustment/tradability + preregistration required
paper_live: coverage + adjustment/tradability + preregistration + separate promotion gate required
```

## Validator

```text
validator_module: src/experiments/research_run_gate_validator.py
test_module: tests/test_research_run_gate_validator.py
real_gate_validation_stage: new_signal_research
real_gate_validation: pass
real_gate_checks: 31 passed / 0 failed
component_provider_coverage_contract: 25 passed / 0 failed
component_adjustment_tradability_policy: 23 passed / 0 failed
component_trial_accounting_preregistration: 36 passed / 0 failed
pytest_target: tests/test_research_run_gate_validator.py tests/test_trial_accounting_preregistration_validator.py tests/test_adjustment_tradability_policy_validator.py tests/test_provider_coverage_contract_validator.py
pytest_result: 20 passed
```

## Required interpretation

The research run gate is an execution precondition. A passing gate does not promote any strategy and does not authorize paper/live trading. It only allows the requested preregistered action to proceed within its already defined limits.

## Next safe step

```text
CREATE_FIRST_PREREGISTERED_PROVIDER_AWARE_RESEARCH_PLAN_SPEC_ONLY
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
