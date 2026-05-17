---
tipo: provider-evaluation-preflight
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: PREFLIGHT_READY_PROVIDER_QUERY_NOT_EXECUTED
provider: Databento Equities Historical
---

# Report Databento Provider Evaluation Preflight - 2026-05-17

## Status

```text
PREFLIGHT READY
PROVIDER QUERY NOT EXECUTED
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

## Governance constraints

No Databento query has been executed by this preflight.

Before any real Databento query:

1. Rotate the pasted Databento API key or confirm it is disposable.
2. Keep key only in local environment variable `DATABENTO_API_KEY`.
3. Confirm account-specific license and raw-response retention rights.
4. Confirm exact cost preview for one tiny historical query.
5. Avoid `ALL_SYMBOLS` for first probe.
6. Use one frozen event, one symbol, tiny time window and very low record limit.
7. Keep `payment_authorized=false` and `payment_cap_usd=0` unless explicitly changed.

## Next allowed step

The next allowed step is a single Databento smoke/micro-probe only after explicit user authorization.

Recommended shape:

```text
one_provider: Databento
one_dataset: EQUS.MINI or documented equivalent
one_schema: trades or OHLCV-compatible schema if available
one_symbol: one frozen DPE event symbol
one_time_window: tiny
raw_retention: false until license confirmed
```
