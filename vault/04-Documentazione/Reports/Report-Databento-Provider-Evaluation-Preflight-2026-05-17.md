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

## Metadata smoke-test and key-source diagnostic update

After a user-side manual smoke-test indicated that `EQUS.MINI` is visible from the Databento Historical account, the probe script was hardened to avoid silent API-key source confusion.

The script now supports:

```text
--api-key-source auto|environment|env-file
--env-file .env
```

Behavior:

```text
auto:
  use process environment if only process environment is set
  use env file if only env file is set
  stop if both are set and fingerprints differ
environment:
  use only the process DATABENTO_API_KEY
env-file:
  use only DATABENTO_API_KEY from the selected env file
```

The rerun with `--api-key-source env-file` confirmed:

```text
api_key_source_resolved: env-file
environment_key_present: false
env_file_key_present: true
api_key_fingerprint: 8cecabc817e0
metadata_smoke_test_result: BentoClientError / 401 auth_authentication_failed
```

Interpretation:

```text
The current repository .env key is the failing credential in this Codex shell.
The failure is not yet evidence against EQUS.MINI availability.
If the user's manual smoke-test passed, the .env key must be updated to the same working Historical key,
or the script must be run from the shell that contains the working key with --api-key-source environment.
```

Interpretation:

```text
DATABENTO_EVALUATION_BLOCKED_BY_AUTHENTICATION
PROVIDER_DATA_NOT_EVALUATED
```

## Successful one-event market-data micro-probe

After key-source diagnostics were hardened and `.env` was corrected, the controlled one-event micro-probe was rerun:

```text
command: .\.venv-lab\Scripts\python.exe experiments\databento_probe_one_event.py --api-key-source env-file
dataset: EQUS.MINI
schema: trades
symbol: FSR
window: 2024-03-20T14:30..2024-03-20T14:35
limit: 10
api_key_source_resolved: env-file
api_key_fingerprint: 6f592453be79
raw_retention: false
```

Result:

```text
status: pass
records_returned: 10
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED
```

Artifact updates:

```text
provider_manifest.json: provider_query_executed=true
provider_event_audit_table.csv: DPE-006 symbol resolves yes, event window available yes
raw_responses_manifest.csv: DPE-006 hash recorded, raw payload not retained
provider_evaluation_summary.md: one-event micro-probe update appended
```

Interpretation:

```text
DATABENTO_ONE_EVENT_MICRO_PROBE_PASS
PROVIDER_DATA_PARTIALLY_EVALUATED_ONE_EVENT_ONLY
RAW_PROVIDER_PAYLOAD_NOT_RETAINED
```

## Dataset diagnostics

After the one-event market-data probe passed, a metadata/symbology/cost diagnostic was executed without raw payload retention:

```text
command: .\.venv-lab\Scripts\python.exe experiments\databento_probe_one_event.py --dataset-diagnostics --api-key-source env-file
status: dataset_diagnostics_pass
dataset: EQUS.MINI
dataset_available: true
dataset_count: 29
schema: trades
schema_available: true
record_count: 10
estimated_cost_usd: 0.000002682209
symbol: FSR
symbology_status: OK
symbology_stype_out: instrument_id
symbology_instrument_id: 6354
```

Available schemas reported for `EQUS.MINI`:

```text
mbp-1
tbbo
trades
bbo-1s
bbo-1m
ohlcv-1s
ohlcv-1m
ohlcv-1h
ohlcv-1d
definition
```

Fields preview for `trades` confirms event-level price/size fields plus timestamps and sequence metadata:

```text
instrument_id
ts_event
price
size
action
side
flags
ts_recv
sequence
```

Interpretation:

```text
DATABENTO_EQUS_MINI_SCHEMA_AND_SYMBOLOGY_OK_FOR_FSR_MICRO_WINDOW
COST_PREVIEW_AVAILABLE_AND_TINY_FOR_LIMIT_10
OHLCV_SCHEMAS_AVAILABLE_FOR_FUTURE_LOW_COST_BAR_PROBES
```

## Governance constraints

No Databento data payload has been retained.

Before any next Databento query:

1. Confirm the current Databento key is valid in the portal.
2. Confirm the key has historical API access attached.
3. Confirm whether the working key is in `.env` or only in the interactive shell.
4. Run the probe with explicit `--api-key-source environment` or `--api-key-source env-file`.
5. Confirm account-specific license and raw-response retention rights.
6. Confirm exact cost preview for one tiny historical query.
7. Avoid `ALL_SYMBOLS` for first probe.
8. Use one frozen event, one symbol, tiny time window and very low record limit.
9. Keep `payment_authorized=false` and `payment_cap_usd=0` unless explicitly changed.

## Next allowed step

The next allowed step is not a broad provider run. If continuing, execute only the next frozen event or a documented schema/symbology check with explicit `--api-key-source env-file`, no `ALL_SYMBOLS`, and no raw retention until licensing/storage rights are confirmed.

Recommended shape:

```text
one_provider: Databento
one_dataset: EQUS.MINI or documented equivalent
one_schema: trades or OHLCV-compatible schema if available
one_symbol: one frozen DPE event symbol
one_time_window: tiny
raw_retention: false until license confirmed
```
