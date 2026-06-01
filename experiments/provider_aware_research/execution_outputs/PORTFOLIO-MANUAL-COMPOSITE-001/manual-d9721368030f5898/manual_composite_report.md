# PORTFOLIO-CANDIDATE-003 Concentration-Repaired Composite

- trial_id: `PORTFOLIO-MANUAL-COMPOSITE-001-D9721368030F5898`
- status: `PORTFOLIO_MANUAL_COMPOSITE_DRY_RUN_COMPLETE`
- decision: `PORTFOLIO_MANUAL_COMPOSITE_DATA_GATE_ONLY`
- promotion_allowed: `false`

## Hypothesis

A fixed-weight four-sleeve composite may be more robust than the original three-sleeve factory basket because it caps the leading sleeve below 40% contribution while combining mean reversion, continuation, and dollar-bar sampling. The claim remains non-promotable until a survivorship-free/PIT data gate is satisfied.

## Sleeves

- **Dollar-bar microstructure sleeve** (Dollar-Bar Microstructure): weight `0.3333` - Use traded-dollar sampling as a stabilizer, not as standalone promotion evidence.
- **Momentum sleeve** (Momentum): weight `0.3333` - Hold diversified continuation candidates only through the frozen multi-day horizon.
- **Mean-reversion sleeve** (Mean Reversion): weight `0.3333` - Buy diversified dislocations after confirmation; do not average down into unresolved continuation.

The three rows above are semantic sleeve families. The executable candidate contract remains a four-component equal-weight basket:

- `a42078cbf0a2ea94` | Mean Reversion | weight `0.25` | core dislocation/recovery sleeve
- `28fb7b03aa56a91e` | Momentum | weight `0.25` | continuation sleeve and breadth diversifier
- `9474fe601e0f2bd2` | Dollar-Bar Microstructure | weight `0.25` | sampling/noise-control sleeve
- `acc065823d9dcfb7` | Momentum | weight `0.25` | continuation sleeve and breadth diversifier

The concentration repair target was satisfied in the frozen local diagnostic: top component contribution fell to `0.36291214`, below the `0.40` ceiling.

## Falsification Criteria

- Archive if Norgate/CRSP-grade survivorship-free data cannot reproduce the component universe with delisted symbols retained.
- Archive if validation/test net return turns negative after current or higher costs.
- Archive if any sleeve contributes more than 40% of positive contribution under true data.
- Archive if ex-best-sleeve net return is non-positive under true data.
- Archive if SPY/IWM/equal-weight benchmark-relative return is not positive after costs.
- Archive if factory/proxy lineage cannot be replaced by a human-authored executable rule contract.

This manifest removes the factory-search label by rewriting the idea as a human hypothesis, but it still cannot promote without a true external-data/PIT gate.
