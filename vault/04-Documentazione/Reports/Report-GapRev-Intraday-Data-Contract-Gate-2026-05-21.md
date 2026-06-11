# Report GapRev Intraday Data Contract Gate - 2026-05-21

## Status

`SPEC_ONLY_NOT_QUERIED`

## Artifact

```text
experiments/provider_aware_research/gap_down_reversion_intraday_data_contract_gate_20260521/
```

## Identity

```text
gate_id: GAPREV-INTRADAY-DATA-CONTRACT-001
trial_id: TRIAL-GAPREV-001
preregistration_id: PREREG-GAPREV-001
gate_decision: GAPREV_INTRADAY_DATA_CONTRACT_PASS
validator: src.experiments.gaprev_intraday_data_contract_validator
checks: 35/35
```

## Purpose

`TRIAL-GAPREV-001` cannot be evaluated with daily OHLCV.

This gate defines the minimum data contract needed before any future intraday extractor, provider query, data download or backtest.

## Required Data Contract

Minimum required:

- intraday bars no coarser than 1 minute for MVP;
- timezone-aware timestamps;
- regular-session filtering;
- half-day and holiday policy;
- prior regular-session close mapping;
- first regular-session open mapping;
- halt/missing-open purge policy;
- spread or quote proxy;
- slippage, market-impact and commission model;
- participation cap;
- raw payload retention disabled by default.

## Current Provider State

No provider is selected by this artifact.

Provider selection, rate limits, retention rights and schema must be approved separately before any query.

## Blocked Actions

```text
select_provider
provider_query
download_intraday_data
implement_extractor
build_intraday_bars
compute_vwap_signals
execute_backtest
run_oos
paper_trading
live_trading
strategy_promotion
```

## Verification

```text
tests/test_gaprev_intraday_data_contract_validator.py
5 passed

tests/test_gap_down_reversion_preregistration_validator.py
5 passed
```

Validation report:

```text
experiments/provider_aware_research/gap_down_reversion_intraday_data_contract_gate_20260521/intraday_data_contract_validation_report.json
status: pass
summary: 35 passed, 0 failed
```

## Decision

The intraday data-contract gate is valid.

The next safe step is a provider-selection gate for intraday bars and spread/quote proxy. No data pull is authorized.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
