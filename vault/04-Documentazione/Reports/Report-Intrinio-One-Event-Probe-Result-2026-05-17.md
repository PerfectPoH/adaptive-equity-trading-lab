---
tipo: provider-evaluation-probe-result
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: AUTHENTICATION_FAILED_PROVIDER_DATA_NOT_EVALUATED
provider: Intrinio Starter Plan
event_id: DPE-006
---

# Report Intrinio One-Event Probe Result - 2026-05-17

## Status

```text
AUTHENTICATION FAILED
PROVIDER DATA NOT EVALUATED
NO RAW RESPONSE RETAINED
NO COST OBSERVED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
NO LIVE / NO PAPER TRADING
```

## Scope

A single minimal Intrinio probe was attempted for one frozen provider-evaluation event.

Target:

```text
event_id: DPE-006
identifier: FSR
window: 2024-03-20..2024-03-28
endpoint_family: Intrinio historical security prices
raw_response_retention: false
payment_cap_usd: 0
credit_card_attached: false
```

## Command

```powershell
.\.venv-lab\Scripts\python.exe experiments\intrinio_probe_one_event.py
```

## Result

The request returned:

```text
HTTP_ERROR_401
Unauthorized
```

After reviewing Intrinio authentication documentation, both supported private-key methods were tried by the user from local PowerShell with a newly generated key:

```text
--auth-method url_param -> HTTP_ERROR_401
--auth-method bearer -> HTTP_ERROR_401
```

Recorded artifact:

```text
experiments/provider_evaluations/intrinio_starter_event_panel_20260517/DPE-006_intrinio_probe_error.json
```

The error artifact redacts the API key:

```text
api_key: REDACTED
```

## Interpretation

This result does not evaluate Intrinio data quality.

It only means the current API credential/session/account state did not authorize the tested historical prices endpoint.

Because both documented private-key authentication methods returned `401`, this is more consistent with an invalid/inactive/provisioning issue for the key/account than with a missing market-data entitlement. Per Intrinio documentation, missing subscription should normally return `403 Forbidden`, not `401 Unauthorized`.

Possible causes include:

- invalid key;
- key not active yet;
- wrong authentication format for endpoint;
- trial not provisioned for this endpoint;
- account requires additional activation;
- endpoint path requires a different identifier or security lookup first.

## Validator result

After the failed probe, the provider evaluation artifact directory still passes the structural validator:

```text
status: pass
failed: 0
passed: 21
total: 21
```

## Next allowed steps

Before any second query:

1. Confirm Intrinio dashboard shows the key as active.
2. Confirm the exact authentication method expected by Intrinio API v2.
3. Confirm the free trial includes historical security prices.
4. Prefer a zero-cost account/status endpoint or documented sample endpoint before probing market data again.
5. Keep `payment_authorized=false` and `payment_cap_usd=0` unless explicitly changed by the user.

## Governance consequence

No provider verdict can be assigned.

Current provider status:

```text
INTRINIO_EVALUATION_BLOCKED_BY_AUTHENTICATION
```
