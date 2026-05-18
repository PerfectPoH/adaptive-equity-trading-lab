# Report - Provider Coverage Contract Spec - 2026-05-18

## Status

```text
PROVIDER_COVERAGE_CONTRACT_REQUIRED_BEFORE_STRATEGY_RUN
SPEC_ONLY_NOT_EXECUTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Purpose

This specification defines the minimum provider coverage contract required before any future small-cap provider-aware strategy research.

It exists because the old yfinance-era results were archived as provider-sensitive. Future research must declare coverage, adjustment, tradability, universe, and licensing assumptions before any execution.

## Required contract fields

```text
contract_id
provider_combo
dataset_or_endpoint
coverage_start
coverage_end
symbol_scope
missingness_policy
adjustment_policy
corporate_action_policy
halt_tradability_policy
PIT_universe_policy
licensing_retention_policy
provider_quality_warnings
stop_conditions
approved_uses
blocked_uses
```

## Enforcement

A provider coverage contract is required before:

```text
data_quality_audit
fixed_signal_replay
new_signal_research
portfolio_backtest
OOS
paper_live_trading
```

The required minimum status becomes stricter as the use case moves closer to performance claims.

## Critical stop conditions

```text
coverage dates not declared
symbol scope not frozen
missingness policy not declared
adjustment policy unknown but performance interpretation requested
PIT universe unknown but universe claim requested
raw retention needed but not licensed
ALL_SYMBOLS query requested
provider warnings silently ignored
```

## Current template stance

For the current Databento Historical + Polygon Free combination:

```text
coverage_start: 2023-03-28
adjustment_policy: raw_or_unknown_caveated
corporate_action_policy: crosscheck_only
halt_tradability_policy: unknown_blocked
PIT_universe_policy: frozen_sample_only
licensing_retention_policy: derived_only
```

## Recommended next implementation step

```text
IMPLEMENT_PROVIDER_COVERAGE_CONTRACT_VALIDATOR
```

The validator should check CSV completeness and block any future strategy run artifact that lacks a valid coverage contract.
