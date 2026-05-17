# 2026-05-17 - Provider evaluation runbook

## Contesto

Dopo provider plan, event panel freeze, expansion, execution checklist, artifact validator e dry-run template, e' stato creato il runbook operativo per il primo giorno di provider evaluation reale.

## Output

Creato [[Report-Provider-Evaluation-Runbook-2026-05-17]].

## Contenuto

Il runbook definisce:

- preconditions;
- secret handling;
- directory creation da dry-run template;
- pre-query edits;
- query sequence `DPE-001..DPE-010`;
- raw response capture;
- snapshot hashing;
- audit row completion;
- provider requirement table completion;
- validator gate;
- provider summary;
- provider-level verdicts;
- execution stop rules;
- git rules;
- post-execution documentation.

## Stato

```text
RUNBOOK READY
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO COST AUTHORIZED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Governance

La prossima azione, se esplicitamente autorizzata, puo' essere una provider evaluation reale su un solo provider alla volta. Anche un provider pass non autorizza trial: abilita solo una futura methodology-gate proposal.
