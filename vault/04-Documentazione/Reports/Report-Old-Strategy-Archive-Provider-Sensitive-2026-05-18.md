# Report - Old Strategy Archive Provider-Sensitive - 2026-05-18

## Decision

```text
OLD_YFINANCE_STRATEGY_RESULTS_ARCHIVED_AS_PROVIDER_SENSITIVE
ARCHIVED_PROVIDER_SENSITIVE_NOT_PROMOTABLE
STRATEGY_PROMOTION_BLOCKED
PAPER_LIVE_TRADING_BLOCKED
```

## Archived strategy reference

```text
setup: breakout_continuation
feature filter: open_to_close_return >= 0.10
regime filter: IWM close > EMA200
sizing: corrected risk_fraction sizing
original provider: yfinance
```

## Evidence basis

The archive decision is based on provider-sensitivity diagnostics, especially the fixed-old-signal Databento replay:

```text
replay_candidates: 66
databento_pass: 66
databento_unavailable_or_error: 0
provider_stable_for_selected_fields: 25
minor_price_or_return_delta: 35
material_price_or_return_delta: 6
max_abs_return_delta: 0.2084676744010346
median_abs_return_delta: 0.0108600878613564
material_delta_symbols: AEHR; AMPX; ARRY; BBAI; NVTS; SANA
```

Supporting evidence:

```text
provider sensitivity micro-check: 4 candidates, caveated
coverage-aware expansion: 8 candidates, provider-sensitive
full-coverage fixed-signal replay: 66 candidates, provider-sensitive
```

## Interpretation

The old yfinance results are not safe to use as performance evidence. They are not proven false as a market hypothesis, but they are provider-sensitive enough that continuing the old track as a validated strategy would be misleading.

A new backtest from the old track would not resolve this, because it would conflate strategy behavior, provider differences, corporate-action handling, and data-quality caveats.

## Required warning

Any future reference to the old results must include:

```text
Old yfinance-era small-cap strategy results are provider-sensitive and cannot be used as performance evidence or promotion basis. Future strategy work must restart as a provider-aware research track with explicit trial accounting.
```

## Allowed reuse

```text
scanner code as infrastructure
portfolio diagnostics as infrastructure
provider sensitivity scripts as diagnostics
methodology reports as historical evidence
```

## Blocked use

```text
strategy promotion
paper trading
live trading
production ranking
continuation backtest framed as validation
OOS framed as validation
parameter sweep to rescue old track
performance claims from old yfinance run
```

## Final status

```text
OLD_STRATEGY_TRACK_CLOSED_NOT_PROMOTABLE
NEXT_STRATEGY_WORK_MUST_BE_NEW_PROVIDER_AWARE_RESEARCH_TRACK
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
