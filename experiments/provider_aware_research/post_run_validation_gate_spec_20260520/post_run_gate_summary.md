# Post-Run Validation Gate

```text
POST_RUN_VALIDATION_GATE_DEFINED
SPEC_ONLY_NOT_EXECUTED
FAIL_CLOSED
```

This gate validates completed research-run artifacts before any interpretation, strategy promotion discussion, or follow-up trial decision.

It does not check whether the strategy made money. Profit is not a pass condition.

It checks whether the run is internally coherent:

1. required run files exist;
2. execution config is present in the manifest;
3. trade log has liquidity, impact, cost and P&L fields;
4. trade-level notional stays inside configured liquidity and impact caps;
5. portfolio summary reconciles with the trade log;
6. outlier diagnostics are present.

Failure means:

```text
BLOCK_INTERPRETATION_AND_PROMOTION
```

The gate performs no provider query, no backtest, no sweep, no paper trading and no live trading.
