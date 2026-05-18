# Report - Trial Accounting Preregistration Spec - 2026-05-18

## Status

```text
TRIAL_ACCOUNTING_AND_PREREGISTRATION_REQUIRED_BEFORE_SIGNAL_RESEARCH
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

This spec prevents p-hacking, continuation bias, silent trial reuse, metric switching, sample redefinition, and parameter expansion after seeing results.

## Required before new signal research

```text
research_question
hypothesis
provider_contract_id
adjustment_tradability_policy_id
sample_definition
in_sample_window
features_allowed
parameters_allowed
primary_metric
secondary_metrics
trial_budget_id
stop_go_threshold_id
forbidden_changes_after_execution
raw_data_retention_policy
```

## Trial accounting stance

```text
new_signal_research: max 3 trials
portfolio_backtest: max 1 trial
OOS: max 1 trial
paper_live: max 1 promotion attempt
reset_allowed: no
```

## Enforcement

```text
new_signal_research: preregistration + trial ledger + budget required
portfolio_backtest: preregistration + trial ledger + budget required
OOS: preregistration + trial ledger + budget required
paper_live: preregistration + trial ledger + budget required + separate promotion gate
```

## Validator

```text
validator_module: src/experiments/trial_accounting_preregistration_validator.py
test_module: tests/test_trial_accounting_preregistration_validator.py
real_spec_validation: pass
real_spec_checks: 36 passed / 0 failed
pytest_target: tests/test_trial_accounting_preregistration_validator.py tests/test_adjustment_tradability_policy_validator.py tests/test_provider_coverage_contract_validator.py
pytest_result: 15 passed
```

## Required interpretation

No new signal research, portfolio backtest, OOS validation, paper trading, or live trading should be interpreted as valid unless it has a valid preregistration, linked provider coverage contract, linked adjustment/tradability policy, trial budget, trial ledger, and predeclared decision threshold.

## Next safe step

```text
IMPLEMENT_RESEARCH_RUN_GATE_VALIDATOR
```
