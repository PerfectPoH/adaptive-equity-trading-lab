# 2026-05-17 - Intrinio provider evaluation preflight

## Contesto

Intrinio Starter Plan e' stato scelto come primo provider candidate per preflight, senza provider query.

## Security

Una API key e' stata incollata in chat. Non e' stata scritta su file e non e' stata usata. Deve essere considerata esposta e ruotata/sostituita prima di qualsiasi query reale.

## Directory creata

```text
experiments/provider_evaluations/intrinio_starter_event_panel_20260517/
```

Derivata dal dry-run template.

## Artifact aggiornati

- `provider_manifest.json`
- `provider_requirement_table.csv`
- `provider_event_audit_table.csv`
- `license_notes.md`
- `query_cost_estimate.md`
- `raw_responses_manifest.csv`
- `provider_evaluation_summary.md`

## Validazione

Comando:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/intrinio_starter_event_panel_20260517
```

Risultato:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Report

Creato [[Report-Intrinio-Provider-Evaluation-Preflight-2026-05-17]].

## Stato

```text
PREFLIGHT READY
PROVIDER QUERY NOT EXECUTED
NO COST AUTHORIZED
NO API KEY STORED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Prossimo blocco

Prima di qualsiasi query reale servono: chiave ruotata/sostituita, payment state confermato, licenza/storage confermati, autorizzazione esplicita al primo probe API.
