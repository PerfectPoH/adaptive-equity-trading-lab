---
tipo: xmom-earnings-provider-selection-gate
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: SPEC_VALIDATED_NOT_QUERIED
---

# Report XMOM Earnings Provider Selection Gate - 2026-05-21

## Scope

Created a provider/data-source gate for the future earnings-event extractor required by `TRIAL-XMOM-CATALYST-001`.

No provider query, network call, market-data download, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Artifacts

```text
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/earnings_provider_selection_manifest.json
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/provider_requirements.csv
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/candidate_provider_roles.csv
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/coverage_quality_policy.csv
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/blocked_actions.csv
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/earnings_provider_selection_summary.md
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/earnings_provider_selection_validation_report.json
```

Validator:

```text
src/experiments/xmom_earnings_provider_selection_validator.py
tests/test_xmom_earnings_provider_selection_validator.py
```

## Result

```text
gate_decision: EARNINGS_PROVIDER_SELECTION_GATE_PASS
passed: 39
failed: 0
```

Targeted tests:

```text
6 passed
```

## Key Invariants

- no provider query;
- no extractor implementation;
- no market-data download;
- no OOS/backtest/paper/live/promotion;
- separate probe approval is required;
- provider must support historical earnings calendar coverage;
- provider must expose or infer report-time quality equivalent to BMO/AMC/DMT/UNSPECIFIED;
- static today-only ticker lists are blocked;
- earnings-only scope remains locked;
- `UNSPECIFIED` and DMT remain purge cases;
- report-time coverage and missingness must be measured before ingestion.

## Decision

The provider-selection gate is structurally valid but not queried.

Next allowed work:

```text
prepare a separate one-provider, one-symbol probe approval artifact
```

Still blocked:

```text
query_provider
implement_extractor
download_market_data
OOS execution
paper/live
strategy_promotion
```

See [[Report-XMOM-Catalyst-Implementation-Gate-Spec-2026-05-20]].
