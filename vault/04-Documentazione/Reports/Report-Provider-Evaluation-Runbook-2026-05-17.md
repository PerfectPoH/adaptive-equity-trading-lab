---
tipo: runbook
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: RUNBOOK_READY_PROVIDER_QUERY_NOT_EXECUTED
scope: provider_evaluation_execution
---

# Report Provider Evaluation Runbook - 2026-05-17

## Status

```text
RUNBOOK READY
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO PRICING DECISION
NO COST AUTHORIZED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Purpose

This runbook defines the exact operator workflow for the first real small-cap data provider evaluation.

It connects:

- [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]]
- [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]]
- [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]]
- [[Report-Small-Cap-Provider-Evaluation-Execution-Checklist-2026-05-17]]
- [[Report-Provider-Evaluation-Artifact-Validator-2026-05-17]]
- [[Report-Provider-Evaluation-Dry-Run-Template-2026-05-17]]

This document does not execute provider evaluation. It is the day-of-execution checklist for when the user explicitly chooses one provider and has valid credentials or free-tier access.

## Hard rule

Only one provider may be evaluated per execution directory.

Do not compare providers until each provider has its own completed, validated artifact directory.

## Preconditions

Before starting real provider evaluation, all of the following must be true:

| Requirement | Required state |
|---|---|
| Frozen event panel | `DPE-001..DPE-010` unchanged |
| Provider candidate | exactly one provider chosen for this execution |
| Account state | account/free trial/free credits confirmed |
| Payment state | no payment or explicit human-approved payment cap |
| API key | available only through local secret handling, never committed |
| Terms/licensing | reviewed and summarized before data pull |
| Storage rights | local research artifact retention allowed or explicitly unclear before stop/continue decision |
| Query budget | estimated before first API call |
| Output directory | copied from dry-run template |
| Stop rules | accepted before execution |

If any item is missing, stop before querying.

## Secret handling

API keys and credentials must never be committed.

Allowed local handling:

```text
.env
PowerShell environment variable
provider portal temporary token copied only into local shell
```

Forbidden:

```text
committing API keys
putting API keys in provider_manifest.json
putting API keys in raw_responses_manifest.csv
putting API keys in Markdown notes
screenshots containing API keys
```

Suggested environment variable naming:

```text
DATABENTO_API_KEY
INTRINIO_API_KEY
POLYGON_API_KEY
TIINGO_API_KEY
```

Only define the variable for the provider currently being evaluated.

## Directory creation

For a real provider, create a new directory from the dry-run template:

```powershell
Copy-Item -Recurse experiments/provider_evaluations/example_provider_event_panel_20260517 experiments/provider_evaluations/<provider_slug>_event_panel_20260517
```

Then replace all dry-run placeholders.

Required output directory pattern:

```text
experiments/provider_evaluations/<provider_slug>_event_panel_20260517/
```

Do not overwrite the dry-run template.

## Pre-query edits

Before any API request, update these files:

### `provider_manifest.json`

Set:

- `provider_name`
- `provider_slug`
- `account_type`
- `payment_authorized`
- `payment_cap_usd`
- `operator`
- `terms_url`
- `license_storage_verdict`
- `data_retention_allowed`
- `dataset_names`
- `api_versions`
- `query_budget_estimate_usd`
- `provider_query_executed: false`

### `license_notes.md`

Record:

- terms URL;
- date accessed;
- allowed use;
- local storage rights;
- redistribution constraints;
- whether raw response retention is allowed;
- whether derived CSV summaries can be committed.

### `query_cost_estimate.md`

Record:

- endpoint names;
- estimated request count;
- rate limits;
- expected credits/units/GB;
- hard stop cap;
- whether a credit card is attached.

If license or cost is unacceptable, stop here.

## Query sequence

For the selected provider, process events in frozen order:

```text
DPE-001
DPE-002
DPE-003
DPE-004
DPE-005
DPE-006
DPE-007
DPE-008
DPE-009
DPE-010
```

For each event, query only what is needed to fill the audit row:

1. identifier/symbol resolution;
2. raw OHLCV for the frozen event window;
3. adjusted OHLCV for the frozen event window, if supported;
4. corporate action metadata;
5. halt/suspension or listing status metadata;
6. delisted/ticker-change history;
7. point-in-time or universe membership support, if provider claims it.

Do not expand the event panel.

Do not replace an event because the provider fails it.

## Raw response capture

If licensing allows local raw response retention, store raw responses under:

```text
experiments/provider_evaluations/<provider_slug>_event_panel_20260517/raw/
```

Recommended names:

```text
DPE-001_identifier.json
DPE-001_raw_ohlcv.json
DPE-001_adjusted_ohlcv.json
DPE-001_corporate_actions.json
DPE-001_halt_listing_status.json
```

If raw response retention is not allowed, record only derived summaries permitted by the license and mark `raw_responses_manifest.csv` accordingly.

## Snapshot hashing

After each artifact is finalized, compute or record a hash in `snapshot_hashes.csv`.

At minimum, hash:

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `provider_evaluation_summary.md`

If raw files are retained, include them in `raw_responses_manifest.csv` with their hashes.

## Audit row completion

For every `DPE-*` row, fill:

```text
provider_symbol_resolves
historical_identifier_stable
event_window_available
raw_ohlcv_available
adjusted_ohlcv_available
corporate_action_metadata_available
halt_or_suspension_visible
delisted_history_available
point_in_time_universe_supported
licensing_allows_research_storage
pipeline_integration_complexity
severity
verdict
notes
```

Allowed verdicts:

```text
pass
caveat
fail
```

A missing, unclear or silently wrong response should not be upgraded to `pass`.

## Provider requirement table completion

Map provider evidence to the hard/soft requirements:

- point-in-time universe;
- delisted symbols;
- corporate actions;
- raw and adjusted prices;
- halt/suspension representation;
- volume integrity;
- API reproducibility;
- licensing/storage;
- cost/limits.

For each requirement, record:

```text
pass
caveat
fail
not_tested
```

## Validator gate

Before interpreting the provider, run:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/<provider_slug>_event_panel_20260517
```

If this fails, do not write a provider verdict.

Fix artifacts or mark the provider evaluation incomplete.

## Provider summary

Only after validator pass, write `provider_evaluation_summary.md` with:

- provider name;
- account type;
- whether payment was used;
- query date/time;
- datasets/endpoints used;
- license/storage verdict;
- query cost actual;
- event pass/caveat/fail counts;
- hard requirement failures;
- critical failures;
- provider-level verdict;
- whether a future methodology gate may be drafted.

## Provider-level verdicts

Use the predeclared verdicts from the evaluation plan.

### `provider_usable_for_small_cap_trials`

Only if:

```text
critical failures = 0
hard requirement failures = 0
>= 80% event rows pass or caveat
delisted symbols covered
reverse splits covered
point-in-time universe support yes or independently available through compatible dataset
license allows research storage/snapshots
```

### `provider_usable_with_caveats`

Only if:

```text
critical failures = 0
hard requirement failures <= 1
>= 60% event rows pass or caveat
all caveats have explicit mitigation plan
no silent survivorship failure
license allows research storage/snapshots
```

### `provider_not_usable`

Triggered by any of:

```text
critical failures >= 1
silent survivorship or delisting failure
no point-in-time universe path
no auditable corporate-action handling
license/storage unclear for reproducible research
< 60% event rows pass or caveat
```

## Stop rules during execution

Stop immediately if:

- provider requires unapproved payment;
- license forbids local research storage/snapshots;
- API key or secret is exposed in an artifact;
- provider silently drops delisted symbols;
- provider cannot distinguish missing, delisted, suspended and normal zero-volume states;
- corporate-action adjustments are undocumented;
- query cost exceeds predeclared cap;
- rate limits make reproducibility infeasible;
- provider coverage tempts replacing frozen events.

## Git rules

Before commit:

```powershell
git status --short
```

Do not commit:

- `.env`
- API keys;
- forbidden raw responses;
- paid-license-restricted files;
- provider portal screenshots with secrets.

Commit only:

- allowed summaries;
- allowed manifests;
- allowed audit tables;
- allowed reports;
- hashes/provenance files that do not leak secrets.

## Required post-execution documentation

If a real provider evaluation is executed, add:

```text
vault/04-Documentazione/Reports/Report-Small-Cap-Data-Provider-Evaluation-Result-YYYY-MM-DD.md
vault/02-Devlog/YYYY-MM/YYYY-MM-DD-cascade-provider-evaluation-result-<provider_slug>.md
```

Update:

- `vault/02-Devlog/Devlog-Index.md`
- `vault/03-Bug/backlog.md`
- `vault/04-Documentazione/Handoff/Project-Handoff.md`
- methodology ledger if a provider pass leads to a proposed new gate.

## Final reminder

A provider pass is necessary but not sufficient.

Even if a provider passes, the next allowed step is a methodology-gate document, not a small-cap strategy trial.
