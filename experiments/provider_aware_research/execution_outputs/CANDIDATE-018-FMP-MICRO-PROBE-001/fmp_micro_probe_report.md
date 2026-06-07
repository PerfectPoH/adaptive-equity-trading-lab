# Candidate 018 FMP Micro-Probe

Decision: `FMP_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE`

Scope: bounded FMP component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.

## Checks

| Case | Symbol | Status | HTTP | Summary |
|---|---|---|---|---|
| `ACTIVE_BASELINE_AAPL` | `AAPL` | `BLOCK` | `403` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |
| `BENCHMARK_SPY` | `SPY` | `BLOCK` | `403` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |
| `BENCHMARK_IWM` | `IWM` | `BLOCK` | `403` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |
| `DELISTED_LIST_US_BBBY` | `BBBY` | `BLOCK` | `403` | `{"contains_required_symbol": false, "row_count": 0, "rows_with_delisting_date_fields": 0, "sample_symbols": []}` |
| `DELISTED_TERMINAL_BBBY` | `BBBY` | `BLOCK` | `403` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |

## Blockers

- `fmp_active_ohlcv_unverified`
- `fmp_spy_benchmark_unverified`
- `fmp_iwm_benchmark_unverified`
- `fmp_delisted_list_unverified`
- `fmp_terminal_ohlcv_unverified`
