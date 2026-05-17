# 2026-05-17 - Provider evaluation artifact validator

## Contesto

Dopo [[Report-Small-Cap-Provider-Evaluation-Execution-Checklist-2026-05-17]], serviva un controllo automatico sugli artifact futuri di provider evaluation.

## TDD

Aggiunto RED test:

```text
tests/test_provider_evaluation_artifact_validator.py
```

RED validato con modulo mancante.

Implementato:

```text
src/experiments/provider_evaluation_artifact_validator.py
```

GREEN mirato:

```text
6 passed
```

## Funzione

CLI:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir <provider_eval_dir>
```

Valida:

- required files;
- `provider_manifest.json` fields;
- payment authorization guardrail;
- required CSV/Markdown readability;
- required `provider_event_audit_table.csv` columns;
- frozen panel coverage `DPE-001..DPE-010`.

## Report

Creato [[Report-Provider-Evaluation-Artifact-Validator-2026-05-17]].

## Governance

Tooling only: nessun provider query, nessun provider selezionato, nessun costo autorizzato, nessun trial small-cap aperto.
