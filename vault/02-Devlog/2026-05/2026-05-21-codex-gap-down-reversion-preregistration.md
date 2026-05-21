# 2026-05-21 - Codex - Gap-down reversion preregistration

## Summary

Opened a new spec-only research branch for intraday gap-down reversion.

## Added

- `experiments/provider_aware_research/gap_down_reversion_preregistration_spec_20260521/`
- `src/experiments/gap_down_reversion_preregistration_validator.py`
- `tests/test_gap_down_reversion_preregistration_validator.py`
- `vault/04-Documentazione/Reports/Report-Gap-Down-Reversion-Preregistration-2026-05-21.md`

## Result

```text
PREREG-GAPREV-001
TRIAL-GAPREV-001
GAPREV_PREREGISTRATION_SPEC_PASS
43/43 checks pass
5/5 targeted tests pass
```

## Safety

No provider query, data download, extractor implementation, parameter sweep, OOS execution, paper/live trading or strategy promotion occurred.

## Next

The clean next gate is an intraday data-contract spec for bars, calendar, corporate actions and spread/quote proxy.
