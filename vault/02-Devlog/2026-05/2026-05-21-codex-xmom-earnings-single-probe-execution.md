# 2026-05-21 - Codex - XMOM earnings single-probe execution

## Summary

Executed the first bounded XMOM earnings metadata provider probe after explicit user approval and a passing preflight.

## What Changed

- Implemented a real execution path in `src/experiments/xmom_earnings_single_probe_runner.py`.
- The runner now performs a single Intrinio earnings metadata request only after all real-run gates are acknowledged and the execution preflight passes.
- Added redacted execution summary handling.
- Added ledger update support for final probe status.
- Recorded explicit approval, output directory and trial ledger artifacts.
- Executed the approved one-call probe for `CRMD`.

## Result

```text
provider: Intrinio
symbol: CRMD
endpoint: companies/{identifier}/upcoming_earnings
status: provider_error_recorded
error: HTTP_ERROR_403
detail: Forbidden
raw_payload_retained: false
```

## Interpretation

The current Intrinio trial/key does not authorize this endpoint/path for the bounded query, or the endpoint requires a different entitlement.

This is a provider-access result, not a strategy result.

## Verification

```text
pytest tests/test_xmom_earnings_single_probe_runner.py tests/test_xmom_earnings_single_probe_execution_preflight_validator.py tests/test_earnings_timestamp_classifier.py
21 passed
```

## Safety

- One provider call executed.
- No raw payload retained.
- No secret disclosed.
- No market-data download.
- No extractor implemented.
- No OOS/backtest/paper/live/promotion.

## Next

Pause provider calls and ask Intrinio which earnings endpoint/entitlement supports the needed historical timestamp metadata.
