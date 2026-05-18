# Intrinio EOD trial onboarding gate

```text
RESEARCH-100
SPEC_ONLY_INTRINIO_TRIAL_INFO_RESOLVED_NOT_QUERIED
NO_API_CALL
NO_MARKET_DATA_DOWNLOAD
NO_BACKTEST
NO_STRATEGY_PROMOTION
NO_RAW_PAYLOAD_RETENTION
```

Intrinio enabled a two-week trial and confirmed EOD with one year of history. Provider follow-up answers resolved coverage and endpoint questions: US small-cap coverage yes, delisted symbols yes, adjusted and unadjusted both available, research/backtesting validation allowed, rate limit 2000 calls per minute, candidate docs are `stock_prices_v2` and `security_historical_data_v2`.

Remaining hard blockers before any query:

```text
ROTATE_OR_REPLACE_INTRINIO_KEY_REQUIRED
SEPARATE_ONE_CALL_PROBE_APPROVAL_REQUIRED
OUTPUT_DIRECTORY_NOT_CREATED
TRIAL_LEDGER_ENTRY_NOT_CREATED
```

Raw payload retention remains disabled by local policy even though derived research use is allowed.
