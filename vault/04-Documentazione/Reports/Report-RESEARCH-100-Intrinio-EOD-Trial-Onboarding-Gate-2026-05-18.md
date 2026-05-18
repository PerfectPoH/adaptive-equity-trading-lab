# Report - RESEARCH-100 Intrinio EOD Trial Onboarding Gate - 2026-05-18

## Status

```text
RESEARCH-100
SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED
INTRINIO_EOD_TRIAL_ONBOARDING_GATE_VALID
NO_API_CALL
NO_NETWORK_CALL
NO_MARKET_DATA_DOWNLOAD
NO_BACKTEST
NO_STRATEGY_PROMOTION
NO_RAW_PAYLOAD_RETENTION
NO_SECRET_DISCLOSURE
```

## Context

Intrinio confirmed that a trial was added to the user account and expires two weeks from the provider reply. The known data offer is:

```text
EOD with one year of history for a trial
```

This gate records the trial opportunity without accessing the account page, reading API docs, reading keys, or querying Intrinio.

## Artifact

```text
experiments/provider_aware_research/intrinio_eod_trial_onboarding_gate_20260518/
```

Files:

```text
intrinio_eod_trial_onboarding_manifest.json
intrinio_trial_terms_checklist.csv
intrinio_eod_endpoint_questions.csv
intrinio_credential_policy.csv
intrinio_probe_budget.csv
intrinio_blocker_register.csv
intrinio_eod_trial_onboarding_summary.md
```

## Critical blocker

The 2026-05-17 Intrinio preflight report states that an Intrinio API key was pasted into chat during earlier setup. Therefore:

```text
ROTATE_OR_REPLACE_INTRINIO_KEY_REQUIRED_BEFORE_ANY_QUERY
```

## First-probe budget, not yet approved

```text
first_probe_symbols: 1
first_probe_provider_calls: 1
raw_payload_retention: false
output_raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
backtest: false
strategy_promotion: false
paper_live: false
```

## Open questions before any API use

```text
endpoint_selection: unresolved
adjustment_policy: unresolved
us_small_cap_coverage: unresolved
delisted_symbol_coverage: unresolved
raw_retention_rights: unresolved
rate_limits: unresolved
separate_probe_approval_missing: unresolved
output_directory_not_created: unresolved
trial_ledger_entry_not_created: unresolved
```

## Validator

```text
validator: 41/41 pass
targeted tests: 16/16 pass
```

## Interpretation

The trial is active and time-limited, but this commit does not consume it. The next safe step is to resolve the open provider questions and rotate or replace the Intrinio key, then create a separate one-call probe approval gate.

## Provider follow-up answers recorded

Intrinio answered the open questions:

```text
US small-cap EOD coverage: yes
Adjusted and unadjusted data: includes both
US exchange support: yes
Delisted symbols: yes
Rate limit: 2000 calls per minute
Suggested docs/endpoints:
  - stock_prices_v2
  - security_historical_data_v2
Internal research/backtesting validation use: yes
```

Updated gate status:

```text
SPEC_ONLY_INTRINIO_TRIAL_INFO_RESOLVED_NOT_QUERIED
INTRINIO_EOD_TRIAL_READY_FOR_ONE_PROBE_PREPARATION_NOT_APPROVED
```

Remaining hard blockers before any query:

```text
prior_key_exposed_in_chat: unresolved
separate_probe_approval_missing: unresolved
output_directory_not_created: unresolved
trial_ledger_entry_not_created: unresolved
```

Validator after provider answers:

```text
intrinio onboarding validator: 42/42 pass
targeted tests: 12/12 pass
```

## Credential replacement recorded

The user stated that the Intrinio API key was changed and placed in local `.env` as:

```text
INTRINIO_API_KEY
```

A presence-only credential preflight was run against `.env`:

```text
status: pass
source: env-file
provider_query_performed: false
network_call_performed: false
secret_values_disclosed: false
value_disclosed: false
```

Updated gate status:

```text
SPEC_ONLY_INTRINIO_CREDENTIAL_READY_NOT_QUERIED
INTRINIO_EOD_TRIAL_READY_FOR_ONE_PROBE_APPROVAL_NOT_EXECUTED
```

Remaining hard blockers:

```text
separate_probe_approval_missing: unresolved
output_directory_not_created: unresolved
trial_ledger_entry_not_created: unresolved
```
