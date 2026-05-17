---
tipo: provider-evaluation-preflight
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: MICRO_PROBE_AUTHENTICATION_FAILED_PROVIDER_DATA_NOT_EVALUATED
provider: Databento Equities Historical
---

# Report Databento Provider Evaluation Preflight - 2026-05-17

## Status

```text
MICRO PROBE ATTEMPTED
AUTHENTICATION FAILED
PROVIDER DATA NOT EVALUATED
NO RAW RESPONSE RETAINED
NO COST OBSERVED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
NO LIVE / NO PAPER TRADING
```

## Context

Databento was selected as the next provider candidate after Intrinio evaluation became blocked by missing active subscription.

User-reported Databento account state:

```text
selected_product_area: equities
selected_mode: historical
free_credits_usd: 125
credit_card_attached: false
api_key_set_locally: true
api_key_stored_in_repo: false
```

A Databento API key was pasted in chat during setup and must be treated as exposed. It was not stored in repository artifacts.

## Preflight directory

Created:

```text
experiments/provider_evaluations/databento_equities_historical_20260517/
```

The directory was copied from the provider-evaluation dry-run template and updated for Databento pre-query state.

## Prepared artifacts

```text
provider_manifest.json
provider_requirement_table.csv
provider_event_audit_table.csv
license_notes.md
query_cost_estimate.md
raw_responses_manifest.csv
snapshot_hashes.csv
provider_evaluation_summary.md
```

## Provider configuration assumptions

```text
provider_name: Databento Equities Historical
provider_slug: databento_equities_historical
account_type: free_credits_no_card_preflight
dataset_candidate: EQUS.MINI
schema_candidate: trades
payment_authorized: false
payment_cap_usd: 0
actual_query_cost_usd: 0
provider_query_executed: false
```

## Validator result

Command:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/databento_equities_historical_20260517
```

Result:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Micro-probe result

After user authorization to use up to `125 USD` of Databento free credits, a single micro-probe script was created and executed:

```text
script: experiments/databento_probe_one_event.py
dataset: EQUS.MINI
schema: trades
symbol: FSR
window: 2024-03-20T14:30..2024-03-20T14:35
limit: 10
raw_retention: false
```

Result:

```text
DATABENTO_ERROR:BentoClientError
401 auth_authentication_failed
Authentication failed.
```

Recorded artifact:

```text
experiments/provider_evaluations/databento_equities_historical_20260517/DPE-006_databento_probe_error.json
```

The error artifact redacts the API key:

```text
api_key: REDACTED
```

Interpretation:

```text
DATABENTO_EVALUATION_BLOCKED_BY_AUTHENTICATION
PROVIDER_DATA_NOT_EVALUATED
```

## Governance constraints

No Databento data payload has been retained.

Before any second Databento query:

1. Confirm the current Databento key is valid in the portal.
2. Confirm the key has historical API access attached.
3. Confirm account-specific license and raw-response retention rights.
4. Confirm exact cost preview for one tiny historical query.
5. Avoid `ALL_SYMBOLS` for first probe.
6. Use one frozen event, one symbol, tiny time window and very low record limit.
7. Keep `payment_authorized=false` and `payment_cap_usd=0` unless explicitly changed.

## Next allowed step

The next allowed step is not another market-data query. First verify key activation/API access in the Databento portal or with a documented account/status/auth smoke test.

Recommended shape:

```text
one_provider: Databento
one_dataset: EQUS.MINI or documented equivalent
one_schema: trades or OHLCV-compatible schema if available
one_symbol: one frozen DPE event symbol
one_time_window: tiny
raw_retention: false until license confirmed
```
