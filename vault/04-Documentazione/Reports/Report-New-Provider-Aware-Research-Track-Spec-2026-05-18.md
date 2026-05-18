# Report - New Provider-Aware Research Track Spec - 2026-05-18

## Status

```text
NEW_PROVIDER_AWARE_RESEARCH_TRACK_REQUIRED
SPEC_ONLY_NOT_EXECUTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Rationale

The old yfinance-era small-cap strategy track has been archived as provider-sensitive. Future strategy research must not continue that track as if it were validated.

A new track is allowed only if provider/data controls are part of the design from the beginning.

## Superseded track

```text
breakout_continuation
open_to_close_return >= 0.10
IWM close > EMA200
corrected risk_fraction sizing
original provider: yfinance
status: archived_provider_sensitive_not_promotable
```

## Required gates before any execution

```text
provider_coverage_contract
adjustment_policy
PIT_universe_policy
halt_tradability_policy
trial_accounting
hypothesis_preregistration
negative_control
provider_sensitivity_check
promotion_policy
```

## Minimum viable next experiment design

A future experiment must include:

```text
one new provider-aware signal hypothesis
small predeclared Databento-covered ticker/date panel
explicit OHLCV/reference/adjustment/coverage policies
random/null baseline
simple holding-window comparator
provider caveat matrix
fixed-signal replay diagnostic
predeclared archive/promote verdict
```

## Blocked work

```text
continuation of old yfinance track
parameter sweep to rescue old results
paper trading
live trading
production ranking
OOS framed as validation before provider-aware in-sample track exists
performance claims from old yfinance run
```

## Allowed work

```text
specification
provider data-quality research
provider coverage contract implementation
adjustment/tradability policy implementation
new hypothesis design with trial accounting
```

## Recommended next step

```text
IMPLEMENT_PROVIDER_COVERAGE_CONTRACT_SPEC
```

This should remain data/methodology infrastructure only. No strategy run should be executed until the required gates pass.
