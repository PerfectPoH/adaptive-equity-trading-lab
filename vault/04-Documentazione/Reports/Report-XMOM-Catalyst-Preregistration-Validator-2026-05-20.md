---
tipo: xmom-catalyst-preregistration-validator
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Catalyst Preregistration Validator - 2026-05-20

## Scope

Implemented and ran a structural validator for the spec-only preregistration:

```text
TRIAL-XMOM-CATALYST-001
PREREG-XMOM-CATALYST-001
```

No backtest, provider query, sweep, paper trading, live trading, Markov/HMM patch or strategy promotion was performed.

## Validator

```text
src/experiments/xmom_catalyst_preregistration_validator.py
```

Test:

```text
tests/test_xmom_catalyst_preregistration_validator.py
```

Validation artifact:

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/spec_validation_report.json
```

## Result

```text
status: pass
gate_decision: SPEC_VALIDATION_PASS
passed: 58
failed: 0
```

## Validated Invariants

The validator checks:

- all required spec files exist;
- Markdown files are readable;
- CSV files are readable;
- `SPEC_ONLY_NOT_EXECUTED` is present;
- trial and preregistration IDs are present;
- no authorization language appears in the spec;
- catalyst taxonomy is frozen;
- `regulatory_fda` is separated from `commercial_rollout`;
- required ex-ante feature families are present;
- feature lookahead policies are strict pre-entry;
- thresholds are not selected from `TRIAL-XMOM-001`;
- feature-threshold rationale remains theory-review-only and not executable;
- candidate threshold parameters remain `not_final`, `TBD` and `not_executable`;
- locked governance thresholds remain fixed;
- promotion rule is blocked;
- robustness and sample-size gates are required;
- Markov/HMM patch, paper/live, strategy promotion and future-news usage are blocked;
- issuer press releases and SEC EDGAR are preferred primary sources;
- forum/social media is blocked as primary evidence.

## Decision

The preregistration package is structurally valid.

It is still not executable.

Allowed next work:

- implementation gate planning only after explicit approval;
- independent threshold-selection design;
- validator extensions for any new spec artifacts before execution.

Blocked:

```text
execute_backtest
run_parameter_sweep
provider_query
paper_trading
live_trading
strategy_promotion
```

See [[Report-XMOM-Catalyst-Trial-001-Preregistration-Spec-2026-05-20]].
