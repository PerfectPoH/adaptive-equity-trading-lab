# Candidate 016 Tiingo Micro-Probe

Decision: `TIINGO_MICRO_PROBE_ADMISSIBLE_COMPONENT`

Scope: bounded Tiingo component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.

## Checks

| Case | Symbol | Status | HTTP | Summary |
|---|---|---|---|---|
| `ACTIVE_BASELINE_AAPL` | `AAPL` | `PASS` | `200` | `{"end_date": "2026-06-05", "field_names": ["description", "endDate", "exchangeCode", "name", "startDate", "ticker"], "start_date": "1980-12-12", "ticker_present": true}` |
| `SPLIT_AAPL_2020` | `AAPL` | `PASS` | `200` | `{"first_date": "2020-08-24", "has_adjusted_close": true, "last_date": "2020-09-04", "non_unit_split_factor_count": 1, "row_count": 10}` |
| `TICKER_CHANGE_FB_META` | `META` | `PASS` | `200` | `{"contains_required_ticker": true, "result_count": 10, "sample_tickers": ["META", "RDMMF", "MTVA", "ONEI", "MTLK", "MLXEF", "MTST", "MRNJ", "MLRT", "BMTLF"]}` |
| `DELISTING_BBBY` | `BBBY` | `PASS` | `200` | `{"first_date": "2023-04-03", "has_adjusted_close": true, "last_date": "2023-05-10", "non_unit_split_factor_count": 0, "row_count": 27}` |
| `BENCHMARK_SPY_IWM_SPY` | `SPY` | `PASS` | `200` | `{"first_date": "2018-01-02", "has_adjusted_close": true, "last_date": "2018-01-10", "non_unit_split_factor_count": 0, "row_count": 7}` |
| `BENCHMARK_SPY_IWM_IWM` | `IWM` | `PASS` | `200` | `{"first_date": "2018-01-02", "has_adjusted_close": true, "last_date": "2018-01-10", "non_unit_split_factor_count": 0, "row_count": 7}` |

## Blockers

- None for Tiingo as component. Candidate 012 still needs a separate fresh-data build gate.
