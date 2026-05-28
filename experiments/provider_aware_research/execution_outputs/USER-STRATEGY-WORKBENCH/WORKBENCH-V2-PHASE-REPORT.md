# Strategy Workbench V2

## Scope

- Added composable rule flow blocks: Universe, Signal, Filter, Entry, Risk, Exit, Gates.
- Added Chart Annotator for generated dry-run trades.
- Added readiness, blueprint, and metric glossary surfaces.

## Governance

- `promotion_allowed` remains false inside the Workbench.
- Dry-runs remain local and diagnostic.
- Real backtests still require a committed pre-run gate, data contract, and separate governed runner.

## Next Phase

- Convert approved strategy blueprints into real pre-run gate packages.
- Connect only selected strategies to real backtest runners after the gate exists.
