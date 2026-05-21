---
tipo: xmom-earnings-single-probe-execution-preflight
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: BLOCKED
---

# Report XMOM Earnings Single Probe Execution Preflight - 2026-05-21

## Scope

Added a pre-execution validator for the future one-provider, one-symbol earnings metadata probe.

This validator checks that the approval gate is valid, explicit approval exists, provider/symbol/endpoint are selected, the immutable output directory is prepared, no execution manifest exists yet, and exactly one pre-execution ledger row matches the approval.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Artifacts

```text
src/experiments/xmom_earnings_single_probe_execution_preflight_validator.py
tests/test_xmom_earnings_single_probe_execution_preflight_validator.py
experiments/provider_aware_research/xmom_earnings_single_probe_execution_preflight_20260521/single_probe_execution_preflight_blocked_report.json
experiments/provider_aware_research/xmom_earnings_single_probe_execution_preflight_20260521/single_probe_execution_preflight_exit_code.txt
experiments/provider_aware_research/xmom_earnings_single_probe_execution_preflight_20260521/README.md
```

## Result

Targeted tests:

```text
6 passed
```

Current real preflight:

```text
status: blocked
decision: XMOM_EARNINGS_SINGLE_PROBE_PREFLIGHT_BLOCKED
passed: 2
failed: 14
exit_code: 1
```

Current blockers are expected:

```text
explicit approval manifest missing
provider not selected
symbol not selected
endpoint not selected
output directory missing
pre-execution manifest missing
trial ledger row missing
```

## Decision

The pre-execution validator is valid and the current probe remains blocked.

Still blocked:

```text
provider query
network call
market-data query
raw payload retention
extractor implementation
OOS execution
paper/live
strategy promotion
```

See [[Report-XMOM-Earnings-Single-Probe-Runner-Gate-2026-05-21]].
