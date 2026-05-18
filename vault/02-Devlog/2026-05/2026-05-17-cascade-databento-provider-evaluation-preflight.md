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

## Micro-probe result

User authorized use of up to `125 USD` free credits. Created `experiments/databento_probe_one_event.py`, installed `databento>=0.78.0`, and attempted one micro-probe:

```text
dataset: EQUS.MINI
schema: trades
symbol: FSR
window: 2024-03-20T14:30..2024-03-20T14:35
limit: 10
raw_retention: false
```

Result:

```text
DATABENTO_ERROR:BentoClientError
401 auth_authentication_failed
Authentication failed.
```

Artifact:

```text
experiments/provider_evaluations/databento_equities_historical_20260517/DPE-006_databento_probe_error.json
```

Provider data not evaluated.

## Successful market-data micro-probe

After `.env` was corrected and user authorized the controlled query, the one-event probe was rerun with explicit key source:

```text
command: .\.venv-lab\Scripts\python.exe experiments\databento_probe_one_event.py --api-key-source env-file
dataset: EQUS.MINI
schema: trades
symbol: FSR
window: 2024-03-20T14:30..2024-03-20T14:35
limit: 10
api_key_source_resolved: env-file
raw_retention: false
```

Result:

```text
status: pass
records_returned: 10
```

Artifact validator after the probe:

```text
status: pass
failed: 0
passed: 21
total: 21
```

Provider data are only partially evaluated for one event. No raw provider payload was retained.

## Key-source diagnostic follow-up

After a user-side manual Historical metadata smoke-test passed for `EQUS.MINI`, the probe script was hardened to disambiguate which key is being used.

Added explicit key source selection:

```text
--api-key-source auto|environment|env-file
--env-file .env
```

Earlier Codex-shell rerun with `--api-key-source env-file`:

```text
api_key_source_resolved: env-file
environment_key_present: false
env_file_key_present: true
api_key_fingerprint: 8cecabc817e0
result: BentoClientError / 401 auth_authentication_failed
```

Interpretation:

```text
The .env key visible to this repo shell at that time was the failing credential.
This does not disprove EQUS.MINI availability.
If the manual smoke-test used a different working key, update .env or rerun with --api-key-source environment.
```

After `.env` was corrected, metadata smoke-test passed and the one-event market-data micro-probe returned `records=10`.

## Dataset diagnostics result

Executed metadata/symbology/cost diagnostics:

```text
command: .\.venv-lab\Scripts\python.exe experiments\databento_probe_one_event.py --dataset-diagnostics --api-key-source env-file
status: dataset_diagnostics_pass
dataset: EQUS.MINI
schema: trades
schema_available: true
record_count: 10
estimated_cost_usd: 0.000002682209
symbol: FSR
symbology_status: OK
symbology_instrument_id: 6354
available_schemas: mbp-1,tbbo,trades,bbo-1s,bbo-1m,ohlcv-1s,ohlcv-1m,ohlcv-1h,ohlcv-1d,definition
```

Interpretation: `EQUS.MINI` is usable for the tested FSR micro-window at metadata/symbology level, and OHLCV schemas are available for future tiny bar probes.
