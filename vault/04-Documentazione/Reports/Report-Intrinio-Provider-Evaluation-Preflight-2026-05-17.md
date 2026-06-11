---
tipo: provider-evaluation-preflight
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: PREFLIGHT_READY_PROVIDER_QUERY_NOT_EXECUTED
provider: Intrinio Starter Plan
---

# Report Intrinio Provider Evaluation Preflight - 2026-05-17

## Status

```text
PREFLIGHT READY
PROVIDER QUERY NOT EXECUTED
PROVIDER SELECTED FOR PREFLIGHT ONLY
NO PRICING DECISION
NO COST AUTHORIZED
NO API KEY STORED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Context

Intrinio Starter Plan was selected as the first provider candidate because its public guide claims active/delisted company and security coverage, historical stock prices, dividends/splits and adjustment factors.

This preflight does not query Intrinio.

## Security note

An API key was pasted into chat during setup. It was not written to repository files and was not used. It must be treated as exposed.

Before any real provider query:

```text
ROTATE_OR_REPLACE_API_KEY_REQUIRED
```

## Preflight directory

```text
experiments/provider_evaluations/intrinio_starter_event_panel_20260517/
```

Created from the dry-run template:

```text
experiments/provider_evaluations/example_provider_event_panel_20260517/
```

## Files prepared

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `snapshot_hashes.csv`
- `provider_evaluation_summary.md`

## Validator result

Command:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/intrinio_starter_event_panel_20260517
```

Result:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Remaining blockers before API query

- Rotate or replace the API key pasted into chat.
- Confirm whether a credit card is attached to the trial account.
- Confirm `payment_authorized=false` and `payment_cap_usd=0` remain correct.
- Confirm Starter Plan trial includes the required endpoints for the frozen panel.
- Confirm local raw response retention and derived artifact commit rights.
- Set the new API key only through local environment variable, not committed files.

Suggested local variable:

```powershell
$env:INTRINIO_API_KEY = "<rotated-key>"
```

## Next allowed step

Only after the blockers above are explicitly resolved, execute the first minimal Intrinio API probe against one frozen event and record all artifacts before expanding to the rest of `DPE-001..DPE-010`.

## Governance consequence

This preflight prepares the first real provider evaluation but does not execute it. A future provider pass remains necessary but not sufficient for any small-cap trial.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
