# WORKBENCH-PORTFOLIO-001 Diagnostic Report

## Verdict

- decision: `PORTFOLIO_RESEARCH_BASKET_CANDIDATE_ONLY`
- promotion_allowed: `False`
- provider_query_performed: `False`
- net_return_sum: `59.04932218`

## Portfolio

- component_count: `298`
- policy: `sleeve_allocation`
- total_net_return: `59.04932218`
- max_drawdown: `-4.12195781`
- max_drawdown_pct_context: `-412.1958`
- time_underwater_ratio: `0.6166583`

## Auto-Clean Basket

- available: `True`
- summary: Remove 201 duplicated component(s). Start with My falsifiable strategy (Catalyst, aeb3c9) because it overlaps with My falsifiable strategy (9:30 AM ORB, ef3f1e).

## Governed Search

- duplicate_groups: `82`
- duplicates_removed: `131`
- candidates_evaluated: `3223`
- best_basket: `['FACTORY-e62a48e2d142923e', 'FACTORY-fab94445f0b51fdf', 'FACTORY-119d99f730b677f6']`
- promotion_allowed: `False`

## Recommended Actions

- `warn` 646 highly correlated component pair(s): Start by removing either My falsifiable strategy (Catalyst, aeb3c9) or My falsifiable strategy (9:30 AM ORB, ef3f1e), then rerun. They appear to be overlapping bets.
- `warn` Data quality keeps this diagnostic-only: Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.

## Governance

This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.
