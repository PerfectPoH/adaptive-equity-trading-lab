# Report Gap-Down Reversion Preregistration - 2026-05-21

## Status

`SPEC_ONLY_NOT_EXECUTED`

## Artifact

```text
experiments/provider_aware_research/gap_down_reversion_preregistration_spec_20260521/
```

## Identity

```text
preregistration_id: PREREG-GAPREV-001
trial_id: TRIAL-GAPREV-001
gate_decision: GAPREV_PREREGISTRATION_SPEC_PASS
validator: src.experiments.gap_down_reversion_preregistration_validator
checks: 43/43
```

## Hypothesis

Extreme overnight gap-downs that show abnormal opening-session volume and reclaim intraday VWAP before a fixed late-morning cutoff may generate positive post-cost intraday mean-reversion under a preregistered trend/liquidity regime.

## Why This Matters

This is the first clean branch opened after the Intrinio earnings endpoint returned `HTTP_ERROR_403`.

It avoids retrying provider calls blindly and moves the lab toward the most operationally defined idea from the latest research notes: intraday gap-down reversion.

## Frozen Scope

- long-only;
- US equities;
- intraday only;
- regular trading hours;
- no overnight holding;
- no shorts;
- no averaging down;
- no paper/live;
- no strategy promotion.

## Allowed Feature Families

- overnight gap return;
- relative opening volume;
- VWAP reclaim flag;
- VWAP reclaim timing;
- macro trend regime;
- Amihud illiquidity;
- spread proxy;
- known catastrophic-event exclusion.

Future holding-window return is explicitly blocked as a feature and may only be used as a label or metric.

## Parameters

Operational thresholds are intentionally not final:

- gap threshold: `TBD_IN_FUTURE_SPEC`;
- relative volume threshold: `TBD_IN_FUTURE_SPEC`;
- VWAP reclaim cutoff: `TBD_IN_FUTURE_SPEC`;
- holding window: `TBD_IN_FUTURE_SPEC`;
- stop policy: `TBD_IN_FUTURE_SPEC`.

The spec therefore cannot be executed.

## Data Requirements

Required before future execution:

- intraday bars;
- corporate-action policy;
- trading calendar;
- spread or quote proxy;
- provider rate-limit contract;
- raw payload retention disabled by default.

PIT universe support is preferred; without it, promotion remains structurally limited.

## Blocked Actions

```text
provider_query
download_intraday_data
implement_extractor
execute_backtest
run_parameter_sweep
run_oos
paper_trading
live_trading
strategy_promotion
reuse_xmom_thresholds
```

## Verification

Targeted tests:

```text
tests/test_gap_down_reversion_preregistration_validator.py
5 passed
```

Validator report:

```text
experiments/provider_aware_research/gap_down_reversion_preregistration_spec_20260521/spec_validation_report.json
status: pass
summary: 43 passed, 0 failed
```

## Decision

`TRIAL-GAPREV-001` is now a valid spec-only research branch.

It is not executable. The next safe step would be a data-contract gate for intraday bars and spread/quote proxy, not a backtest.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
