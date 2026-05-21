---
tipo: xmom-earnings-single-probe-runner-gate
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: DRY_RUN_AVAILABLE_REAL_RUN_BLOCKED
---

# Report XMOM Earnings Single Probe Runner Gate - 2026-05-21

## Scope

Added a gated inert runner for the future earnings-calendar/report-time single probe.

The runner can produce a dry-run plan and a blocked real-run report, but it does not contain any provider-query implementation path. The current real-run state is blocked because explicit probe approval has not been granted and provider/symbol/output/ledger inputs remain unresolved.

## Artifacts

```text
src/experiments/xmom_earnings_single_probe_runner.py
tests/test_xmom_earnings_single_probe_runner.py
experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/single_probe_runner_dry_run_plan.json
experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/single_probe_runner_real_run_block_report.json
experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/real_run_exit_code.txt
experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/README.md
```

## Result

Targeted tests:

```text
5 passed
```

Dry-run:

```text
status: dry_run_only
provider_query_performed: false
network_call_performed: false
extractor_implemented: false
```

Real-run gate:

```text
status: blocked
error: single_probe_real_run_gates_unresolved
exit_code: 2
```

Missing gates:

```text
explicit_single_probe_approval_granted
provider_selected
symbol_selected
endpoint_selected
immutable_output_directory_created
trial_ledger_entry_created
raw_payload_retention_blocked
```

## Decision

The runner gate is valid as a safety layer and remains non-executable.

Still blocked:

```text
provider query
market-data query
raw payload retention
extractor implementation
OOS execution
paper/live
strategy promotion
```

See [[Report-XMOM-Earnings-Single-Probe-Approval-2026-05-21]].
