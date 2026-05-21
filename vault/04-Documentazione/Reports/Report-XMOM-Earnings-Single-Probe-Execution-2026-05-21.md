# Report XMOM Earnings Single-Probe Execution - 2026-05-21

## Status

`PROVIDER_ERROR_RECORDED`

## Scope

- Gate: `EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001`
- Trial: `TRIAL-XMOM-CATALYST-001`
- Provider: `Intrinio`
- Symbol: `CRMD`
- Endpoint: `companies/{identifier}/upcoming_earnings`
- Provider call budget: `1`
- Raw payload retention: `false`

## Preflight

The execution preflight passed before the provider call:

```text
XMOM_EARNINGS_SINGLE_PROBE_PREFLIGHT_PASS_READY_FOR_APPROVED_EXECUTION
checks: 21/21
failed: 0
```

Pre-execution artifacts created:

- `experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_20260521/`
- `experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001/`
- `experiments/provider_aware_research/trial_ledger/xmom_earnings_single_probe_trial_ledger.csv`

## Execution Result

The single approved provider query was performed and returned:

```text
HTTP_ERROR_403
detail: Forbidden
```

Execution manifest:

```text
experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001/single_probe_execution_manifest.json
```

The manifest is redacted and contains no secret values.

## Interpretation

This is a provider/access verdict, not a strategy verdict.

The result means the current Intrinio trial/key does not authorize the selected earnings endpoint for this bounded query, or the endpoint requires a different entitlement/path than the one available in the account.

No timestamp-quality conclusion can be drawn because no earnings records were returned.

## Safety Flags

```text
provider_query_performed: true
network_call_performed: true
market_data_downloaded: false
raw_payload_retained: false
extractor_implemented: false
backtest_performed: false
strategy_promotion_performed: false
api_key: REDACTED
```

## Governance Outcome

The gate behaved correctly:

- approval was required before the call;
- preflight passed before execution;
- only one provider call was attempted;
- no raw payload was retained;
- the same output artifact now blocks a second execution by default.

## Next Decision

Do not retry blindly.

Allowed next steps:

- ask Intrinio whether `companies/{identifier}/upcoming_earnings` is included in the current trial;
- request the correct entitlement or endpoint for historical/expected earnings dates with timestamp/report-time metadata;
- open a new one-call approval artifact only after the provider answers.

Blocked:

- repeated calls against the same output artifact;
- endpoint guessing loops;
- extractor implementation;
- OOS/backtest/paper/live/promotion.
