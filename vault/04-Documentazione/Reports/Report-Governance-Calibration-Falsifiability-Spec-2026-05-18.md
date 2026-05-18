# Report - Governance Calibration Falsifiability Spec - 2026-05-18

## Status

```text
GOVERNANCE_CALIBRATION_FALSIFIABILITY_DEFINED_NOT_RUN
SPEC_ONLY_NOT_EXECUTED
VALIDATOR_IMPLEMENTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_STRATEGY_PROMOTION
```

## User concern

The concern was whether the governance layer might create such a strong barrier that any strategy would fail by construction.

## Calibration answer

The governance layer should block unsafe, under-specified, non-reproducible, or post-hoc research. It should not require positive returns, perfect data, or permanent parameter immutability.

## Key design separation

```text
hard governance constraints: may block execution, must not block positive result by definition
research design choices: may affect empirical result, can change only via new preregistration
performance conclusions: allowed only after future empirical execution, not from validators
```

## Anti-overconstraint checks

```text
FAL-001: at least one allowed execution path exists after approval/preflight
FAL-002: positive and negative empirical outcomes are both representable
FAL-003: performance thresholds are not embedded in provider validators
FAL-004: research-design parameters can change via new preregistration
FAL-005: synthetic compliant artifacts can pass governance without implying alpha
```

## Red flags tracked

```text
no_execution_path_even_with_approval
validators_require_positive_return
trial_budget_zero
all_parameter_changes_permanently_forbidden
coverage_requirement_demands_perfect_data
promotion_block_used_as_research_block
```

## Validator

```text
validator_module: src/experiments/governance_calibration_validator.py
test_module: tests/test_governance_calibration_validator.py
real_calibration_validation: pass
real_calibration_checks: 38 passed / 0 failed
focused_pytest_result: 25 passed
```

## Required interpretation

A governance pass is not alpha evidence. A governance fail is not strategy failure unless the failure is empirical and preregistered. Governance failure means the test is not safe or specified enough to interpret.

## Direct answer

The current framework is not intended to make every strategy fail. It is intended to make unregistered, under-specified, provider-fragile, or non-reproducible claims fail. The calibration spec now makes that distinction enforceable.

## Next safe step

```text
IMPLEMENT_DRY_RUN_PREFLIGHT_VALIDATOR_SPEC_ONLY
```
