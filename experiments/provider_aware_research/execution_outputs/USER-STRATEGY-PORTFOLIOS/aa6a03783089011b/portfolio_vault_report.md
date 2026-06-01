# WORKBENCH-PORTFOLIO-001 Diagnostic Report

## Verdict

- decision: `PORTFOLIO_ARCHIVE_CONCENTRATION_FAILED`
- promotion_allowed: `False`
- provider_query_performed: `False`
- net_return_sum: `12.16586`

## Portfolio

- component_count: `3`
- policy: `sleeve_allocation`
- total_net_return: `12.16586`
- max_drawdown: `-3.863992`
- max_drawdown_pct_context: `-386.3992`
- time_underwater_ratio: `0.89799636`

## Auto-Clean Basket

- available: `False`
- summary: No automatic de-duplication suggested.

## Governed Search

- duplicate_groups: `0`
- duplicates_removed: `0`
- candidates_evaluated: `1`
- best_basket: `['dcfbeec9cf4c5190', 'bcfc1ff3b7cf8a4a', '9c7fb1982851f609']`
- promotion_allowed: `False`

## Recommended Actions

- `block` Failed because return is too concentrated: Reduce the top contributor weight or add genuinely different components before rerunning.
- `warn` 1 highly correlated component pair(s): Start by removing either My falsifiable strategy (Momentum, bcfc1f) or strategia folle (PDUFA Run-Up, dcfbee), then rerun. They appear to be overlapping bets.
- `block` One component dominates the portfolio: Remove or cap strategia folle (PDUFA Run-Up, dcfbee), then add at least two components from different sleeves before rerunning.
- `warn` Data quality keeps this diagnostic-only: Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.

## Governance

This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.
