# Public Catalyst Hybrid Coverage Audit 001

## Verdict

`PUBLIC_CATALYST_HYBRID_COVERAGE_AUDIT_BLOCKS_PROMOTION`

This is a read-only audit of the rerun artifacts. No provider query, no market-data download, no new backtest, and no promotion.

## Coverage

- Panel rows: `34`
- Admissible events: `33`
- Mature admissible events as of 2026-06-01: `23`
- Covered mature admissible events: `19`
- Missing mature admissible events: `4`
- Mapping complication events: `6`

## Result Reconciliation

- Original rerun weighted net return sum: `1.198761`
- Valid-as-of weighted net return sum: `1.198761`
- Immature/future weighted contribution: `0.000000`
- Valid-as-of trade count: `57`
- Immature/future trade count: `0`
- Valid-as-of win rate: `0.5965`

## Missing Mature Price Coverage

- EXP-PDUFA-015 `TLX.AX`: ValueError
- EXP-PDUFA-018 `KRTX`: ValueError
- EXP-PDUFA-019 `DCPH`: ValueError
- EXP-PDUFA-023 `ORCA-PRIVATE`: ValueError

## Future Or Immature Trade Windows Detected

- none

## Interpretation

The expanded catalyst idea remains interesting, but the rerun cannot be interpreted as a validated backtest. The valid-as-of slice is the only defensible subset as of 2026-06-01, and even that subset remains blocked by incomplete coverage, unresolved delisted/acquired symbols, and manual panel construction.

## Next Action

Build a stricter rerun runner that enforces `as_of_date` and excludes immature event windows before calculating returns. Only after that should the portfolio candidate consume this catalyst sleeve.
