# 2026-05-17 - Databento provider evaluation preflight

## Contesto

Dopo il blocco Intrinio per `No active subscription(s)`, e' stata preparata una preflight Databento per equity historical data.

User-reported state:

```text
provider: Databento
selected_product_area: equities
selected_mode: historical
free_credits_usd: 125
credit_card_attached: false
```

## Output

Creata directory:

```text
experiments/provider_evaluations/databento_equities_historical_20260517/
```

Aggiornati artifact:

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

## Validazione

Comando:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir experiments/provider_evaluations/databento_equities_historical_20260517
```

Risultato:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Report

Creato [[Report-Databento-Provider-Evaluation-Preflight-2026-05-17]].

## Stato

```text
PREFLIGHT_READY
PROVIDER_QUERY_NOT_EXECUTED
NO_RAW_RESPONSE_RETAINED
NO_COST_OBSERVED
NO_STRATEGY_TRIAL_OPENED
NO_BACKTEST / NO_OOS / NO_SWEEP
```

## Note sicurezza

Una Databento API key e' stata incollata in chat durante setup e deve essere trattata come esposta. Nessuna chiave e' stata salvata nel repository.

## Prossimo step

Prima query ammessa solo dopo autorizzazione esplicita: one-provider, one-event, one-symbol, tiny window, low limit, no raw retention fino a conferma licenza/storage.
