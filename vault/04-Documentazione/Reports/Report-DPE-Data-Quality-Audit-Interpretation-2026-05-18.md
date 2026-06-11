# Report - DPE Data-Quality Audit Interpretation - 2026-05-18

## Status

```text
DATA_QUALITY_AUDIT_INTERPRETATION_EXECUTED
NO_NEW_PROVIDER_QUERY
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_LIVE_TRADING
NO_PAPER_TRADING
```

## Input layer

```text
experiments/provider_evaluations/dpe_data_quality_audit_layer_20260518/dpe_panel_derived_feature_table.csv
experiments/provider_evaluations/dpe_data_quality_audit_layer_20260518/event_window_availability_matrix.csv
experiments/provider_evaluations/dpe_data_quality_audit_layer_20260518/corporate_action_crosscheck_matrix.csv
```

## Observed coverage

```text
DPE events: 10
symbol_resolves_yes: 10 / 10
event_window_available_yes: 10 / 10
verdict_pass: 0 / 10
verdict_caveat: 10 / 10
verdict_fail: 0 / 10
critical_or_high_caveats: 7 / 10
```

Databento Historical resolves and returns event-window data for all frozen DPE events. Polygon Free improves cross-check coverage for selected recent splits, dividends, ticker details and delisted/reference cases.

## Blocking gaps

```text
adjustment_factors: blocked by paid Databento Reference subscription
full PIT universe: blocked
full security master: blocked
halt feed: not validated
offering metadata: not covered by current providers
raw payload storage rights: unclear
Polygon aggregate access: HTTP 403 observed for DJT minute aggregate
Polygon history depth: 2-year plan constraint
```

## Interpretation

The provider combo is materially better than `yfinance` daily alone for the adversarial DPE panel because it recovers historical event windows that yfinance failed to provide in earlier audits. However, it is not a final institutional-quality provider foundation because all DPE rows remain caveated and the most important anti-lookahead/reference requirements remain unresolved.

The correct conclusion is not that the data foundation is ready for strategy performance evaluation. The correct conclusion is that the foundation is ready for controlled data-quality and provider-join feasibility work.

## Methodological verdict

```text
USABLE_FOR_DATA_QUALITY_AUDIT_WITH_CAVEATS
NOT_USABLE_FOR_STRATEGY_PERFORMANCE_CLAIMS
TRIALS_REMAIN_BLOCKED
```

## Required warning for future artifacts

Any future artifact that uses this provider combo must include:

```text
Provider data caveat: Databento Historical + Polygon Free is approved only for data-quality audit and provider-join feasibility. It does not provide validated adjusted factors, full point-in-time universe membership, full security master continuity, validated halt feed, offering metadata, or raw storage rights. Strategy trials, backtests, OOS, sweeps, live trading and paper trading remain blocked.
```

## Allowed next work

```text
PROVIDER_JOIN_FEASIBILITY_CHECK
DATA_QUALITY_WARNING_INTEGRATION
METHODOLOGY_GATE_DRAFT_WITH_PROVIDER_CAVEATS
```

## Disallowed next work

```text
SMALL_CAP_STRATEGY_TRIAL
BACKTEST
OOS_VALIDATION
PARAMETER_SWEEP
PAPER_TRADING
LIVE_TRADING
RAW_PROVIDER_PAYLOAD_STORAGE
ALL_SYMBOLS_SCREENING
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
