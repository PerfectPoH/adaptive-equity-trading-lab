# Intrinio EOD trial onboarding gate

```text
RESEARCH-100
SPEC_ONLY_INTRINIO_CREDENTIAL_READY_NOT_QUERIED
NO_API_CALL
NO_MARKET_DATA_DOWNLOAD
NO_BACKTEST
NO_STRATEGY_PROMOTION
NO_RAW_PAYLOAD_RETENTION
NO_SECRET_DISCLOSURE
```

Intrinio enabled a two-week trial and confirmed EOD with one year of history. Provider follow-up answers resolved coverage and endpoint questions: US small-cap coverage yes, delisted symbols yes, adjusted and unadjusted both available, research/backtesting validation allowed, rate limit 2000 calls per minute, candidate docs are `stock_prices_v2` and `security_historical_data_v2`.

Credential rotation blocker is resolved: the user stated a new Intrinio key was placed in `.env` as `INTRINIO_API_KEY`, and a presence-only env-file credential preflight passed without value disclosure or network call.

Remaining hard blockers before any query:

```text
SEPARATE_ONE_CALL_PROBE_APPROVAL_REQUIRED
OUTPUT_DIRECTORY_NOT_CREATED
TRIAL_LEDGER_ENTRY_NOT_CREATED
```

Raw payload retention remains disabled by local policy even though derived research use is allowed.
