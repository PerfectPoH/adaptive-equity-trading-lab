# Devlog - RESEARCH-100 Intrinio EOD Trial Onboarding Gate - 2026-05-18

Created a spec-only onboarding gate for the active Intrinio EOD trial.

```text
RESEARCH-100
SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED
NO_API_CALL
NO_MARKET_DATA_DOWNLOAD
NO_RAW_PAYLOAD_RETENTION
NO_SECRET_DISCLOSURE
```

The gate captures the provider reply: the trial is active for two weeks and can provide EOD with one year of history. It also records the critical blocker from the earlier Intrinio preflight: the previously pasted key must be rotated or replaced before any query.

Validation:

```text
intrinio onboarding validator: 41/41 pass
targeted tests: 16/16 pass
```
