# Polygon PIT Construction Method Gate - 2026-05-24

No-query method gate for point-in-time membership construction.

The gate defines the membership rule:

`list_date <= as_of_date < delisted_date`

For active securities with no delisting date, membership is true for as-of dates on or after `list_date`. For delisted securities, membership is false on and after the delisting date. This run may construct only a sample membership table from already archived derived metadata. It may not query providers, download market data, run backtests, sweep parameters, execute trades, or promote a strategy.

