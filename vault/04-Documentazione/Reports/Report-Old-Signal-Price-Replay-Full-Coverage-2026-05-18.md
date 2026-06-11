# Report - Old Signal Price Replay Full Coverage - 2026-05-18

## Status

```text
OLD_SIGNAL_PRICE_REPLAY_FULL_COVERAGE_DIAGNOSTIC_EXECUTED
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_NEW_SIGNAL_GENERATION
NO_PORTFOLIO_BACKTEST
NO_EQUITY_CURVE
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Scope

This diagnostic replays fixed old yfinance-era executed signals using Databento daily OHLCV prices where the signal date is inside the Databento/EQUS.MINI coverage window.

It does not generate new signals and does not evaluate portfolio performance. It only compares old yfinance entry/exit prices and returns against Databento-derived entry/exit prices and returns for the same symbol/date windows.

## Results

```text
replay_candidates: 66
databento_pass: 66
databento_unavailable_or_error: 0
provider_stable_for_selected_fields: 25
minor_price_or_return_delta: 35
material_price_or_return_delta: 6
provider_unavailable: 0
max_abs_entry_delta_pct: 0.0738547538964422
max_abs_exit_delta_pct: 0.1457489745829387
max_abs_return_delta: 0.2084676744010346
median_abs_return_delta: 0.0108600878613564
material_delta_symbols: AEHR;AMPX;ARRY;BBAI;NVTS;SANA
```

Databento emitted dataset-condition warnings for some 2025 windows marked as degraded. These warnings are retained as methodological caveats, not raw payloads.

## Verdict

```text
OLD_SIGNAL_RETURNS_PROVIDER_SENSITIVE_FULL_COVERAGE_REPLAY
OLD_YFINANCE_RESULTS_REQUIRE_PROVIDER_SENSITIVITY_WARNING
OLD_STRATEGY_RESULTS_NOT_SAFE_FOR_PROMOTION
```

## Interpretation

The old yfinance-era fixed signals are fully replayable on the Databento-covered subset, but the resulting price/return comparison is not provider-stable.

A majority of rows are either stable or minor-delta, but 6 of 66 rows show material price/return deltas above the pre-declared 5% threshold. The largest absolute return delta is approximately 20.85%.

This is enough to treat old yfinance results as provider-sensitive. A portfolio backtest would not clarify strategy quality unless the data foundation is rebuilt provider-aware.

## Allowed conclusion

```text
The old yfinance signal results are provider-sensitive on the Databento-covered subset and require a warning before any future use.
```

## Blocked conclusion

```text
The strategy works.
The strategy fails.
Databento validates the old yfinance backtest.
The old result can be promoted to paper trading.
```

## Next safe step

```text
ARCHIVE_OLD_STRATEGY_RESULTS_AS_PROVIDER_SENSITIVE
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
