# Intrinio EOD trial onboarding gate

```text
RESEARCH-100
SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED
NO_API_CALL
NO_MARKET_DATA_DOWNLOAD
NO_BACKTEST
NO_STRATEGY_PROMOTION
NO_RAW_PAYLOAD_RETENTION
```

Intrinio has enabled a two-week trial on the user account and offered EOD data with one year of history. This gate records the opportunity and blocks all API usage until credential rotation, endpoint/terms/rate-limit clarification, output/ledger preparation, and a separate one-probe approval are complete.

Important blocker: the 2026-05-17 Intrinio preflight report states that an API key was pasted into chat during earlier setup. A rotated or replaced key is required before any Intrinio query.
