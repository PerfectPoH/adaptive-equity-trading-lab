---
tipo: xmom-earnings-single-probe-explicit-approval-template
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: TEMPLATE_VALIDATED_NOT_GRANTED
---

# Report XMOM Earnings Single Probe Explicit Approval Template - 2026-05-21

## Scope

Created a template-only explicit approval package for a future one-provider, one-symbol earnings metadata probe.

This template is intentionally separate from the live approval directory used by the execution preflight:

```text
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_20260521/
```

That live approval directory still does not exist, so the probe remains blocked.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Artifacts

```text
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/explicit_approval_template_manifest.json
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/approval_fields_required.csv
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/pre_execution_package_checklist.csv
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/blocked_until_approval.csv
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/README.md
experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/explicit_approval_template_validation_report.json
```

Validator:

```text
src/experiments/xmom_earnings_single_probe_explicit_approval_template_validator.py
tests/test_xmom_earnings_single_probe_explicit_approval_template_validator.py
```

## Result

```text
decision: XMOM_EARNINGS_SINGLE_PROBE_EXPLICIT_APPROVAL_TEMPLATE_PASS
passed: 30
failed: 0
approval_granted: false
```

Targeted tests:

```text
6 passed
```

## Decision

The template is valid, but it is not an approval.

Still blocked:

```text
copy_to_live_approval_dir
create_output_directory
create_trial_ledger_entry
execute_probe
query_provider
save_raw_payload
implement_extractor
run_oos
paper/live
strategy_promotion
```

See [[Report-XMOM-Earnings-Single-Probe-Execution-Preflight-2026-05-21]].
