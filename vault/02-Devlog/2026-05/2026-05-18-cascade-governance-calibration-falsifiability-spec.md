# Devlog - Governance calibration falsifiability spec - 2026-05-18

Created a governance calibration and falsifiability spec to address the concern that the provider-aware governance stack might overconstrain every strategy by construction.

```text
GOVERNANCE_CALIBRATION_FALSIFIABILITY_DEFINED_NOT_RUN
SPEC_ONLY_NOT_EXECUTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_STRATEGY_PROMOTION
```

Added `src/experiments/governance_calibration_validator.py` and `tests/test_governance_calibration_validator.py`.

Validation: calibration artifact passes 38/38 and focused pytest target passes 25/25.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
