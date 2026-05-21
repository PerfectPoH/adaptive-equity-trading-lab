# 2026-05-21 - Codex - GapRev intraday data-contract gate

## Summary

Added a spec-only intraday data-contract gate for `TRIAL-GAPREV-001`.

## Added

- `experiments/provider_aware_research/gap_down_reversion_intraday_data_contract_gate_20260521/`
- `src/experiments/gaprev_intraday_data_contract_validator.py`
- `tests/test_gaprev_intraday_data_contract_validator.py`
- `vault/04-Documentazione/Reports/Report-GapRev-Intraday-Data-Contract-Gate-2026-05-21.md`

## Result

```text
GAPREV_INTRADAY_DATA_CONTRACT_PASS
35/35 checks pass
10 targeted tests pass with prereg validator
```

## Safety

No provider was selected.

No provider query, network call, data download, extractor implementation, backtest, OOS, paper/live or promotion occurred.

## Next

Create a provider-selection gate for intraday bars and spread/quote proxy.
