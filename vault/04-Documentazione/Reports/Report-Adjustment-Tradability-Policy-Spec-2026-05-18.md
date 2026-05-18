# Report - Adjustment Tradability Policy Spec - 2026-05-18

## Status

```text
ADJUSTMENT_TRADABILITY_POLICY_REQUIRED_BEFORE_PERFORMANCE_RESEARCH
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

This policy defines how price adjustment, corporate actions, halt/tradability, point-in-time universe, licensing retention, and provider-quality warnings gate future provider-aware small-cap research.

## Current policy stance

```text
price_adjustment: raw_or_unknown_caveated
corporate_actions: crosscheck_only
halt_tradability: unknown_blocked
PIT_universe: frozen_sample_only
licensing_retention: derived_only
provider_quality_warnings: must_capture_as_caveat
```

## Performance research status

```text
portfolio_backtest: blocked until performance_policy_gate_passed
OOS: blocked until in-sample provider-aware track and policy gate pass
paper_live: blocked until all policy gates and separate promotion gate pass
```

## Critical stop conditions

```text
adjustment_policy_unknown_and_performance_requested
corporate_action_source_missing_for_adjusted_claim
halt_tradability_unknown_for_small_cap_execution
PIT_universe_missing_for_universe_claim
raw_retention_required_without_license
```

## Validator

```text
validator_module: src/experiments/adjustment_tradability_policy_validator.py
test_module: tests/test_adjustment_tradability_policy_validator.py
real_policy_validation: pass
real_policy_checks: 23 passed / 0 failed
pytest_target: tests/test_adjustment_tradability_policy_validator.py tests/test_provider_coverage_contract_validator.py
pytest_result: 10 passed
```

## Required interpretation

The current Databento/Polygon research stack may support diagnostics with caveats, but it does not yet support performance research or strategy promotion.

## Next safe step

```text
IMPLEMENT_TRIAL_ACCOUNTING_AND_PREREGISTRATION_SPEC
```
