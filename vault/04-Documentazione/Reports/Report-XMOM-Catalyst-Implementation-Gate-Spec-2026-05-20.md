---
tipo: xmom-catalyst-implementation-gate-spec
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: SPEC_VALIDATED_NOT_EXECUTABLE
---

# Report XMOM Catalyst Implementation Gate Spec - 2026-05-20

## Scope

Converted the research note on DSR, CPCV, purging/embargoing and blind ECDF threshold selection into a formal implementation gate package:

```text
IMPL-GATE-XMOM-CATALYST-001
TRIAL-XMOM-CATALYST-001
```

No OOS execution, provider query, parameter sweep, paper trading, live trading or strategy promotion was performed.

## Artifacts

```text
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/README.md
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/implementation_gate_spec.md
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/implementation_gate_manifest.json
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/phase_contract.csv
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/blind_threshold_policy.csv
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/validation_math_policy.csv
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/blocked_actions.csv
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/source_review.csv
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520/implementation_gate_validation_report.json
```

Validator:

```text
src/experiments/xmom_catalyst_implementation_gate_validator.py
tests/test_xmom_catalyst_implementation_gate_validator.py
```

## Result

```text
gate_decision: IMPLEMENTATION_GATE_SPEC_PASS
passed: 47
failed: 0
```

Targeted tests:

```text
5 passed
```

## Key Invariants

- status remains `SPEC_ONLY_NOT_EXECUTABLE`;
- OOS execution remains blocked;
- provider query remains blocked;
- candidate thresholds remain blind to returns and not executable;
- CPCV, purging, embargoing, trial accounting and DSR are required;
- `DSR >= 0.95` is required before any future promotion discussion;
- failure after a final OOS pass cannot be repaired by a second OOS sweep;
- informal sources are blocked as primary evidence.

## Important Interpretation

The implementation gate does not say the catalyst-aware hypothesis is valid.

It only says the future implementation path is valid enough to prevent the most obvious research failure modes:

```text
curve fitting
OOS contamination
unlogged trial search
manual override after DSR failure
threshold selection from old winners
```

## Decision

The gate spec is structurally valid but not executable.

Next allowed work:

- implement reusable DSR/PSR math utilities with unit tests;
- implement CPCV split utilities with synthetic leakage tests;
- design an effective trial-count estimator;
- still no OOS execution.

Blocked:

```text
execute_oos
query_oos_provider_data
parameter_sweep
paper_trading
live_trading
strategy_promotion
```

See [[Report-XMOM-Catalyst-Feature-Rationale-2026-05-20]].
