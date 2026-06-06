# Candidate 013 Databento Fresh Data Entitlement Probe

Decision: `DATABENTO_FRESH_DATA_BLOCKED_REFERENCE_ENTITLEMENT`

Scope: bounded metadata/reference entitlement probe only. No market-data download, no dataset build, no backtest.

## Historical Metadata

- Status: `PASS`
- `EQUS.MINI`: status `PASS`, schema_available `True`, tiny_cost `1.564622e-06`, tiny_record_count `1`
- `EQUS.SUMMARY`: status `PASS`, schema_available `True`, tiny_cost `1.564622e-06`, tiny_record_count `1`

## Reference Metadata

- Overall: `BLOCKED_REFERENCE_ENTITLEMENT`
- `corporate_actions`: `BLOCKED_403`
- `security_master`: `BLOCKED_403`
- `adjustment_factors`: `BLOCKED_403`

## Blockers

- `databento_reference_entitlement_missing`
