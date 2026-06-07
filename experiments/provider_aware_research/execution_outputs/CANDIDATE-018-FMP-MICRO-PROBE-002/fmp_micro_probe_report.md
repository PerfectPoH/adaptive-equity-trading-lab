# Candidate 018 FMP Micro-Probe

Decision: `FMP_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE`

Scope: bounded FMP component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.

## Checks

| Case | Symbol | Status | HTTP | Summary |
|---|---|---|---|---|
| `ACTIVE_BASELINE_AAPL` | `AAPL` | `BLOCK` | `200` | `{"first_date": "2020-08-24", "has_adjusted_close": false, "has_ohlcv": true, "last_date": "2020-09-04", "row_count": 10}` |
| `BENCHMARK_SPY` | `SPY` | `BLOCK` | `200` | `{"first_date": "2018-01-02", "has_adjusted_close": false, "has_ohlcv": true, "last_date": "2018-01-10", "row_count": 7}` |
| `BENCHMARK_IWM` | `IWM` | `BLOCK` | `402` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |
| `DELISTED_LIST_US_BBBY` | `BBBY` | `PASS` | `200` | `{"contains_required_symbol": false, "row_count": 100, "rows_with_delisting_date_fields": 100, "sample_symbols": ["AGAE", "EDAP", "BTMWW", "AMWD", "6201.T", "1726.T", "ZBAI", "CVGW", "4384.T", "D6H.DE", "OTH", "7925.T", "6489.T", "GIG", "POR.V", "BTM", "CTBB", "QVCC", "BWEB", "BTOP"]}` |
| `DELISTED_TERMINAL_BBBY` | `BBBY` | `BLOCK` | `402` | `{"first_date": null, "has_adjusted_close": false, "has_ohlcv": false, "last_date": null, "row_count": 0}` |

## Blockers

- `fmp_active_ohlcv_unverified`
- `fmp_spy_benchmark_unverified`
- `fmp_iwm_benchmark_unverified`
- `fmp_terminal_ohlcv_unverified`
