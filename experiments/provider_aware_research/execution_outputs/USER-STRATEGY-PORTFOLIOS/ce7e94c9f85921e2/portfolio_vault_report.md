# WORKBENCH-PORTFOLIO-001 Diagnostic Report

## Verdict

- decision: `PORTFOLIO_ARCHIVE_COST_STRESS_FAILED`
- promotion_allowed: `False`
- provider_query_performed: `False`
- net_return_sum: `26.66744239`

## Portfolio

- component_count: `40`
- policy: `sleeve_allocation`
- total_net_return: `26.66744239`
- max_drawdown: `-7.43152444`
- max_drawdown_pct_context: `-743.1524`
- time_underwater_ratio: `0.74985722`

## Auto-Clean Basket

- available: `True`
- summary: Remove 8 duplicated component(s). Start with My falsifiable strategy (9:30 AM ORB, ef3f1e) because it overlaps with My falsifiable strategy (Catalyst, aeb3c9).

## Governed Search

- duplicate_groups: `5`
- duplicates_removed: `5`
- candidates_evaluated: `3223`
- best_basket: `['bc79985845236f4a', '7d30471f7325a2a8', 'acc065823d9dcfb7']`
- promotion_allowed: `False`

## Recommended Actions

- `block` Failed because costs erase the basket: Lower turnover, use longer holding periods, or test execution assumptions before trusting the result.
- `warn` 11 highly correlated component pair(s): Start by removing either My falsifiable strategy (Catalyst, aeb3c9) or My falsifiable strategy (9:30 AM ORB, ef3f1e), then rerun. They appear to be overlapping bets.
- `warn` Data quality keeps this diagnostic-only: Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.

## Governance

This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.
