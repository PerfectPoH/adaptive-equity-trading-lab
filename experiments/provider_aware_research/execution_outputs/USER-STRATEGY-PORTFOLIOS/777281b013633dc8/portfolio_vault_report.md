# WORKBENCH-PORTFOLIO-001 Diagnostic Report

## Verdict

- decision: `PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY`
- promotion_allowed: `False`
- provider_query_performed: `False`
- net_return_sum: `63.67377365`

## Portfolio

- component_count: `298`
- policy: `sleeve_allocation`
- total_net_return: `63.67377365`
- max_drawdown: `-3.9792313`
- max_drawdown_pct_context: `-397.9231`
- time_underwater_ratio: `0.58061325`

## Auto-Clean Basket

- available: `True`
- summary: Remove 201 duplicated component(s). Start with My falsifiable strategy (Catalyst, aeb3c9) because it overlaps with My falsifiable strategy (9:30 AM ORB, ef3f1e).

## Governed Search

- duplicate_groups: `79`
- duplicates_removed: `178`
- candidates_evaluated: `3223`
- best_basket: `['FACTORY-e62a48e2d142923e', 'FACTORY-fab94445f0b51fdf', 'FACTORY-119d99f730b677f6']`
- promotion_allowed: `False`

## Recommended Actions

- `block` Factory search is diagnostic-only: Convert the generated components into explicit Workbench manifests, pre-register them, and rerun before reading candidate status.
- `warn` 646 highly correlated component pair(s): Start by removing either My falsifiable strategy (Catalyst, aeb3c9) or My falsifiable strategy (9:30 AM ORB, ef3f1e), then rerun. They appear to be overlapping bets.
- `warn` Data quality keeps this diagnostic-only: Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.

## Governance

This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.
