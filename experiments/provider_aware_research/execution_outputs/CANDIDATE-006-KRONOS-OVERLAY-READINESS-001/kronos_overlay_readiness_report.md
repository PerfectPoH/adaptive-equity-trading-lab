# Candidate 006 Kronos Overlay Readiness 001

Decision: `CANDIDATE_006_KRONOS_OVERLAY_READINESS_BLOCKED_INSUFFICIENT_FEATURE_COVERAGE`

Scope: readiness diagnostic only. No new inference, no backtest, no threshold optimization, no promotion.

## Coverage

- Trade rows: `37`
- Feature rows: `1`
- Trade symbols: `32`
- Feature symbols: `1`
- Symbol coverage ratio: `0.0`
- Trade-row coverage ratio: `0.0`
- Rebalance-date coverage ratio: `0.0`

## Interpretation

The archived Kronos smoke proves the model can emit features, but it is not broad enough to touch Candidate 005.
Using one SPY forecast to rerank a 37-trade, 282-symbol recovery breadth basket would be an overfitting trap.

## Blockers

- `single_symbol_kronos_smoke_not_overlay_admissible`
- `kronos_feature_unique_symbol_count_below_contract`
- `kronos_feature_unique_date_count_below_contract`
- `kronos_symbol_coverage_below_contract`
- `kronos_trade_row_coverage_below_contract`
- `kronos_rebalance_date_coverage_below_contract`
- `kronos_feature_coverage_below_contract`

## Next Allowed Action

`Create a separate batch Kronos feature-generation gate with frozen symbol/date coverage before any overlay backtest.`
