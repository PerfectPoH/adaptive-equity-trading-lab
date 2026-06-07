# Candidate 017 EODHD Micro-Probe

Decision: `EODHD_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE`

Scope: bounded EODHD component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.

## Checks

| Case | Symbol | Status | HTTP | Summary |
|---|---|---|---|---|
| `DELISTED_LIST_US_BBBY` | `BBBY` | `BLOCK` | `200` | `{"contains_required_symbol": false, "row_count": 57823, "sample_symbols": ["0P0000V6X4", "0P0001UM32", "AAAB", "AAADX", "AAAEX", "AAAFX", "AAAGY", "AAAHX", "AAAID", "AAAIF", "AAAJX", "AAAKX", "AAALF", "AAALX", "AAALY", "AAAP", "AAARF", "AAAWX", "AAB", "AABA"]}` |
| `DELISTED_TERMINAL_BBBY` | `BBBY.US` | `PASS` | `200` | `{"first_date": null, "has_adjusted_close": false, "last_date": null, "row_count": 1}` |
| `ACTIVE_BASELINE_AAPL` | `AAPL.US` | `PASS` | `200` | `{"first_date": null, "has_adjusted_close": false, "last_date": null, "row_count": 1}` |

## Blockers

- `eodhd_delisted_list_unverified`
