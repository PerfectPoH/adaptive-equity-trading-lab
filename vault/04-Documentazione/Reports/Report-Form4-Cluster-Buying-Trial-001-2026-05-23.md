# Report Form 4 Cluster Buying Trial 001 - 2026-05-23

Decision: `FORM4_CLUSTER_BUYING_ARCHIVE_CURRENT_FORM`

## Scope

Official SEC EDGAR Form 4 query bounded to AEHR, ARRY, CABA, CRMD and IOVA. Only derived transaction rows were retained. No raw SEC payload, market-data download, parameter sweep, short selling, paper/live trading, or promotion occurred.

## Result

- Derived transaction count: 0
- Event cluster count: 0
- Completed trade count: 0
- Gross return sum: 0
- Net return sum after 500 bps: 0
- Median net return: 0.0
- Net win rate: 0.0
- Net return sum ex-top3: 0.0
- Symbols traded: 
- Blockers: sec_provider_query_error, event_count_below_5, trade_count_below_5, net_return_not_positive_after_500bps, median_net_return_not_positive

## Interpretation

This is a long-only Form 4 cluster buying diagnostic. A positive result may only become a candidate for separate validation; it cannot promote a strategy in this run.
