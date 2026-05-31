# WORKBENCH-PORTFOLIO-001 Diagnostic Report

## Verdict

- decision: `PORTFOLIO_ARCHIVE_COST_STRESS_FAILED`
- promotion_allowed: `False`
- provider_query_performed: `False`
- net_return_sum: `31.68414076`

## Portfolio

- component_count: `39`
- policy: `sleeve_allocation`
- total_net_return: `31.68414076`
- max_drawdown: `-8.6071287`
- max_drawdown_pct_context: `-860.7129`
- time_underwater_ratio: `0.73397075`

## Recommended Actions

- `block` Failed because costs erase the basket: Lower turnover, use longer holding periods, or test execution assumptions before trusting the result.
- `warn` 7 highly correlated component pair(s): Start by removing either My falsifiable strategy or 9:15, then rerun. They appear to be overlapping bets.
- `warn` Data quality keeps this diagnostic-only: Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.

## Governance

This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.
