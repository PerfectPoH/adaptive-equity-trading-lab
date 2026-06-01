# Separate Portfolio Trial Dry-Run: PORTFOLIO-TRIAL-737154C8E0DA2306

- status: `SEPARATE_PORTFOLIO_TRIAL_DRY_RUN_COMPLETE`
- decision: `PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY`
- promotion_allowed: `false`
- blockers: `factory_generated_scope_gate, component_concentration_gate`

This artifact is a dry-run only. It does not authorize paper trading, live trading, provider queries, or promotion.

## Basket Tested

- `a42078cbf0a2ea94` | Factory Mean Reversion 180d 100bps | weight `0.60` | source `factory_materialized`
- `FACTORY-e62a48e2d142923e` | Factory Momentum 180d 100bps | weight `0.20` | source `factory_generated`
- `FACTORY-119d99f730b677f6` | Factory Dollar-Bar Microstructure 180d 100bps | weight `0.20` | source `factory_generated`

## Diagnostic Summary

- component_count: `3`
- total_net_return: `480.4254534`
- max_drawdown: `-3.7512214`
- time_underwater_ratio: `0.45163869`
- top_component_contribution: `0.60954173`
- high_correlation_pair_count: `0`
- period_count: `1251`
- policy: `sleeve_allocation`

## Why It Did Not Promote

1. `factory_generated_scope_gate`: two components are generated factory recipes, not separately governed strategy trials. They can guide research, but they are not admissible live evidence.
2. `component_concentration_gate`: the strongest component contributes about `60.95%` of the positive basket contribution, above the `40%` concentration ceiling. The basket is still too dependent on one sleeve.

## Interpretation

This is an interesting research lead, not a deployable portfolio. The correlation check did not find hidden duplicate bets, which is good. The problem is provenance and concentration: before any stronger claim, the generated Momentum and Dollar-Bar sleeves must become separately pre-registered/materialized components, and the Mean Reversion sleeve must stop dominating the basket.
