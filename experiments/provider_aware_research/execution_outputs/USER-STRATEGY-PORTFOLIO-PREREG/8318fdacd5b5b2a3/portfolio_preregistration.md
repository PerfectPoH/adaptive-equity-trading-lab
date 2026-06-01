# Portfolio Pre-Registration Draft: PORTFOLIO-PREREG-8318FDACD5B5B2A3

- status: `PREREGISTRATION_DRAFT_REQUIRES_MANUAL_APPROVAL`
- manual approval required: `true`
- promotion_allowed: `false`
- paper_trading_allowed: `false`
- live_trading_allowed: `false`

## Hypothesis

A bounded basket of separately governed strategy components may be more robust than any single component after costs, duplicate removal, correlation checks, and ex-best stress.

## Selected Components

- `28fb7b03aa56a91e` | Factory Momentum 180d 100bps | Momentum | source `factory_materialized`
- `FACTORY-fab94445f0b51fdf` | Factory Mean Reversion 180d 100bps | Mean Reversion | source `factory_generated`
- `FACTORY-6a8afca3951761f9` | Factory Catalyst 180d 100bps | Catalyst | source `factory_generated`
- `FACTORY-119d99f730b677f6` | Factory Dollar-Bar Microstructure 180d 100bps | Dollar-Bar Microstructure | source `factory_generated`

## Anti-Overfit Disclosures

- `selected_after_search`
- `portfolio_diagnostic_only`
- `promotion_locked_false`
- `factory_generated_scope`
- `component_bias_warnings_present`

## Falsification Criteria

- Archive if the basket fails after removing the strongest component.
- Archive if cost stress at 1.5x declared costs flips the net result negative.
- Archive if a single component contributes more than 40% of positive contribution.
- Archive if high correlation shows the basket is a hidden duplicate bet.
- Archive or keep diagnostic-only if any component still depends on factory-generated/proxy data.

## Required Next Step

User must manually approve this draft, then rerun as a separately pre-registered portfolio trial before interpreting candidate status.