---
tipo: xmom-earnings-single-probe-approval
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: SPEC_VALIDATED_NOT_QUERIED
---

# Report XMOM Earnings Single Probe Approval - 2026-05-21

## Scope

Created a single-provider, single-symbol probe approval artifact for the future earnings-calendar/report-time metadata probe required before any earnings extractor can be implemented for `TRIAL-XMOM-CATALYST-001`.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Artifacts

```text
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_approval_manifest.json
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_scope.csv
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/expected_probe_output_schema.csv
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_stop_rules.csv
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_blocked_actions.csv
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_approval_summary.md
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_approval_validation_report.json
```

Validator:

```text
src/experiments/xmom_earnings_single_probe_approval_validator.py
tests/test_xmom_earnings_single_probe_approval_validator.py
```

## Result

```text
gate_decision: EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_PASS
passed: 38
failed: 0
```

Targeted tests:

```text
8 passed
```

## Key Invariants

- the probe is not authorized;
- provider and symbol remain `unselected`;
- explicit separate approval is required;
- maximum scope is one provider, one symbol, one endpoint and one provider call;
- raw payload retention is blocked;
- derived/redacted output schema is required;
- stop rules force halt on auth error, rate limit, raw-payload need, secret detection, missing report-time support, or scope widening;
- provider query, price-volume query, extractor implementation, OOS execution, paper/live trading and strategy promotion remain blocked.

## Decision

The single-probe approval artifact is structurally valid and ready for future human review, but it does not grant permission to query a provider.

Next allowed work only after explicit approval:

```text
create a bounded one-call probe runner/output directory/ledger entry
```

Still blocked:

```text
provider query
price-volume query
raw payload retention
extractor implementation
OOS execution
paper/live
strategy promotion
```

See [[Report-XMOM-Earnings-Provider-Selection-Gate-2026-05-21]].
