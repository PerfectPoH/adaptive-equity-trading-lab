---
tipo: tooling-report
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: IMPLEMENTED_TDD
scope: provider_evaluation_artifact_validation
---

# Report Provider Evaluation Artifact Validator - 2026-05-17

## Status

```text
IMPLEMENTED WITH TDD
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO PRICING DECISION
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Purpose

This report documents the provider-evaluation artifact validator added after [[Report-Small-Cap-Provider-Evaluation-Execution-Checklist-2026-05-17]].

The validator checks that future provider-evaluation output directories contain the required reproducibility and governance artifacts before any result is interpreted.

## CLI

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir <provider_eval_dir>
```

Exit codes:

| Exit code | Meaning |
|---:|---|
| 0 | validation pass |
| 1 | validation fail |

## Required files

The validator requires:

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `snapshot_hashes.csv`
- `provider_evaluation_summary.md`

## Manifest checks

`provider_manifest.json` must include the fields defined in the execution checklist, including:

- `provider_name`
- `provider_slug`
- `account_type`
- `payment_authorized`
- `payment_cap_usd`
- `execution_date`
- `operator`
- `frozen_panel_report`
- `panel_expansion_report`
- `terms_url`
- `license_storage_verdict`
- `data_retention_allowed`
- `dataset_names`
- `api_versions`
- `query_budget_estimate_usd`
- `actual_query_cost_usd`
- `provider_query_executed`

The validator explicitly fails if `payment_authorized` is `true`. This keeps any future paid execution outside accidental tooling flow and requires explicit human authorization before cost-bearing work.

## Event audit checks

`provider_event_audit_table.csv` must include all required audit columns from the checklist and must cover the frozen panel exactly:

```text
DPE-001..DPE-010
```

Missing or extra event IDs fail validation.

## TDD evidence

RED test file:

```text
tests/test_provider_evaluation_artifact_validator.py
```

RED result:

```text
ModuleNotFoundError: No module named 'src.experiments.provider_evaluation_artifact_validator'
```

GREEN targeted result:

```text
6 passed
```

Targeted command:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests/test_provider_evaluation_artifact_validator.py -q
```

## Governance consequence

This is tooling hardening only. It does not query providers, select providers, authorize costs or open small-cap trials.
