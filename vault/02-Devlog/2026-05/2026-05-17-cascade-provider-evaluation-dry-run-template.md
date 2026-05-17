# 2026-05-17 - Provider evaluation dry-run template

## Contesto

Dopo l'implementazione di `src.experiments.provider_evaluation_artifact_validator`, e' stato creato un template dry-run per verificare end-to-end lo schema artifact di una futura provider evaluation.

## Directory creata

```text
experiments/provider_evaluations/example_provider_event_panel_20260517/
```

## File inclusi

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `snapshot_hashes.csv`
- `provider_evaluation_summary.md`

## Validazione

Comando:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/example_provider_event_panel_20260517
```

Risultato:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Report

Creato [[Report-Provider-Evaluation-Dry-Run-Template-2026-05-17]].

## Governance

Template only: nessun provider query, nessun provider selezionato, nessun costo autorizzato, nessun trial small-cap aperto.
