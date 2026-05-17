# 2026-05-17 - Intrinio one-event probe result

## Contesto

Dopo preflight Intrinio, e con user-confirmed state `credit_card_attached=false` e `payment_cap_usd=0`, e' stato creato uno script per un singolo micro-probe su `DPE-006 / FSR`.

## Script

Creato:

```text
experiments/intrinio_probe_one_event.py
```

Lo script legge `INTRINIO_API_KEY` da variabile d'ambiente, non stampa la chiave e redige eventuali artifact di errore con `api_key: REDACTED`.

## Esecuzione

Comando:

```powershell
.\.venv-lab\Scripts\python.exe experiments\intrinio_probe_one_event.py
```

Risultato:

```text
HTTP_ERROR_401
Unauthorized
```

## Artifact

Creato:

```text
experiments/provider_evaluations/intrinio_starter_event_panel_20260517/DPE-006_intrinio_probe_error.json
```

## Validazione

Il provider evaluation directory passa ancora il validator:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Report

Creato [[Report-Intrinio-One-Event-Probe-Result-2026-05-17]].

## Stato

```text
AUTHENTICATION FAILED
PROVIDER DATA NOT EVALUATED
NO RAW RESPONSE RETAINED
NO COST OBSERVED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Prossimo blocco

Verificare dashboard Intrinio, attivazione chiave, metodo auth API v2 e coverage del trial prima di un secondo probe.
