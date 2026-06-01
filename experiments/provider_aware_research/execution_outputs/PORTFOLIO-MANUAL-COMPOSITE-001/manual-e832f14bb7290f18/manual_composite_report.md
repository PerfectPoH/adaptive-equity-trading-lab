# Multi-Horizon Reversion Momentum Catalyst Basket

- trial_id: `PORTFOLIO-MANUAL-COMPOSITE-002-E832F14BB7290F18`
- status: `PORTFOLIO_MANUAL_COMPOSITE_DRY_RUN_COMPLETE`
- decision: `PORTFOLIO_MANUAL_COMPOSITE_DATA_GATE_ONLY`
- promotion_allowed: `false`

## Hypothesis

A fixed-weight basket combining reversion, continuation, and dollar-sampled microstructure may be more robust than a single setup, but only if it survives a survivorship-free/PIT data gate.

## Sleeves

- **Momentum sleeve** (Momentum): weight `0.2500` - Hold diversified continuation candidates only through the frozen multi-day horizon.
- **Mean-reversion sleeve** (Mean Reversion): weight `0.2500` - Buy diversified dislocations after confirmation; do not average down into unresolved continuation.
- **Catalyst sleeve** (Catalyst): weight `0.2500` - Keep the component rule frozen and treat it as one bounded sleeve inside the composite.
- **Dollar-bar microstructure sleeve** (Dollar-Bar Microstructure): weight `0.2500` - Use traded-dollar sampling as a stabilizer, not as standalone promotion evidence.

## Falsification Criteria

- Archive if external-data/PIT gate cannot be satisfied.
- Archive if validation net turns negative under the true data source.
- Archive if one sleeve contributes more than 40% of positive contribution under true data.
- Archive if ex-best-sleeve net return is non-positive under true data.
- Archive if benchmark-relative return is not positive after costs.

This manifest removes the factory-search label by rewriting the idea as a human hypothesis, but it still cannot promote without a true external-data/PIT gate.