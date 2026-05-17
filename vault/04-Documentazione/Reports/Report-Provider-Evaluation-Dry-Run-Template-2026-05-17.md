---
tipo: tooling-report
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: DRY_RUN_TEMPLATE_VALIDATED
scope: provider_evaluation_artifact_template
---

# Report Provider Evaluation Dry-Run Template - 2026-05-17

## Status

```text
DRY_RUN_TEMPLATE_VALIDATED
PROVIDER_QUERY_NOT_EXECUTED
NO PROVIDER_SELECTED
NO PRICING_DECISION
NO COST_AUTHORIZED
NO STRATEGY_TRIAL_OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Purpose

This report documents the dry-run provider-evaluation artifact template created after [[Report-Provider-Evaluation-Artifact-Validator-2026-05-17]].

The objective is to prove that the provider-evaluation checklist can be materialized into concrete files that pass the artifact validator before any real provider query.

## Template directory

```text
experiments/provider_evaluations/example_provider_event_panel_20260517/
```

## Template files

The directory contains:

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `snapshot_hashes.csv`
- `provider_evaluation_summary.md`

All files are placeholders explicitly marked as dry-run artifacts.

## Validation command

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/example_provider_event_panel_20260517
```

## Validation result

```text
status: pass
failed: 0
passed: 21
total: 21
```

Key checks passed:

- required file presence;
- manifest required fields;
- payment authorization guardrail;
- CSV readability;
- Markdown readability;
- required provider-event audit columns;
- exact frozen panel coverage `DPE-001..DPE-010`.

## Interpretation

The template is not evidence about any provider. It only verifies that future provider-evaluation artifact directories can follow the required schema.

## Governance consequence

This is tooling/scaffolding only. It does not query providers, select providers, authorize costs or open any small-cap strategy trial.
