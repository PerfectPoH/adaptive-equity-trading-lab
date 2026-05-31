# Strategy Workbench V2

## Scope

- Added composable rule flow blocks: Universe, Signal, Filter, Entry, Risk, Exit, Gates.
- Added Chart Annotator for generated dry-run trades.
- Added readiness, blueprint, and metric glossary surfaces.

# Strategy Workbench V3

## Scope

- Added governed strategy package generation.
- Package includes strategy manifest, pre-run gate, data contract, command spec, risk policy, README, and dry-run report.
- Package generation remains non-executing and cannot authorize paper/live trading.
- Added Package Inspector to review saved packages before building any real runner.
- Added first local diagnostic package runner that consumes a saved package and emits final_decision.json.

## Governance

- `promotion_allowed` remains false inside the Workbench.
- Dry-runs remain local and diagnostic.
- Real backtests still require a committed pre-run gate, data contract, and separate governed runner.
- Strategy packages keep `execution_allowed=false` and `promotion_allowed=false`.
- Package Inspector can mark a package ready for runner build, but not ready for execution.
- Diagnostic runner performs local artifact generation only; provider, paper, live, and promotion remain forbidden.

## Next Phase

- Convert approved strategy blueprints into real pre-run gate packages.
- Connect only selected strategies to real backtest runners after the gate exists.
