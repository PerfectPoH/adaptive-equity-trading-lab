# Portfolio Pre-Registration Draft: PORTFOLIO-PREREG-CANDIDATE-002-8AE940FAFF3F492A

- status: `PREREGISTRATION_DRAFT_REQUIRES_MANUAL_APPROVAL`
- manual approval required: `true`
- promotion_allowed: `false`
- paper_trading_allowed: `false`
- live_trading_allowed: `false`

## Hypothesis

A bounded basket of separately governed strategy components may be more robust than any single component after costs, duplicate removal, correlation checks, and ex-best stress.

## Selected Components

- `FACTORY-e62a48e2d142923e` | Factory Momentum 180d 100bps | Momentum | source `factory_generated`
- `FACTORY-fab94445f0b51fdf` | Factory Mean Reversion 180d 100bps | Mean Reversion | source `factory_generated`
- `FACTORY-6a8afca3951761f9` | Factory Catalyst 180d 100bps | Catalyst | source `factory_generated`
- `FACTORY-119d99f730b677f6` | Factory Dollar-Bar Microstructure 180d 100bps | Dollar-Bar Microstructure | source `factory_generated`

## Anti-Overfit Disclosures

- `component_bias_warnings_present`
- `factory_generated_scope`
- `iterative_search_after_candidate_001`
- `portfolio_diagnostic_only`
- `promotion_locked_false`
- `selected_after_search`

## Falsification Criteria

- Archive if the basket fails after removing the strongest component.
- Archive if cost stress at 1.5x declared costs flips the net result negative.
- Archive if a single component contributes more than 40% of positive contribution.
- Archive if high correlation shows the basket is a hidden duplicate bet.
- Archive or keep diagnostic-only if any component still depends on factory-generated/proxy data.

## Required Next Step

User must manually approve this draft, then rerun as a separately pre-registered portfolio trial before interpreting candidate status.