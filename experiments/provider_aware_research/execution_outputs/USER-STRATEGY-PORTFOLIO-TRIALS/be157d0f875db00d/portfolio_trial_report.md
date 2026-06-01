# Separate Portfolio Trial Dry-Run: PORTFOLIO-TRIAL-BE157D0F875DB00D

- status: `SEPARATE_PORTFOLIO_TRIAL_DRY_RUN_COMPLETE`
- decision: `PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY`
- promotion_allowed: `false`
- blockers: `factory_generated_scope_gate, component_concentration_gate`

This artifact is a dry-run only. It does not authorize paper trading, live trading, provider queries, or promotion.

## Materialized Basket Tested

- `a42078cbf0a2ea94` | Factory Mean Reversion 180d 100bps | source `factory_materialized`
- `28fb7b03aa56a91e` | Factory Momentum 180d 100bps | source `factory_materialized`
- `9474fe601e0f2bd2` | Factory Dollar-Bar Microstructure 180d 100bps | source `factory_materialized`

## Diagnostic Summary

- component_count: `3`
- total_net_return: `480.4254534`
- max_drawdown: `-12.2183118`
- top_component_contribution: `0.60954173`

## Interpretation

This rerun replaced the two raw factory-generated component ids from draft `737154c8e0da2306` with saved Workbench materialized artifacts. That removes the unsaved recipe problem, but it does not make the basket promotable: the components still carry factory lineage and proxy-data warnings, so the `factory_generated_scope_gate` remains active.

The second blocker is independent and more important for construction: the strongest sleeve still contributes about `60.95%` of positive portfolio contribution. A real portfolio candidate needs either lower Mean Reversion concentration, a fourth genuinely independent sleeve, or a true external-data/PIT test showing the concentration is not a proxy artifact.
