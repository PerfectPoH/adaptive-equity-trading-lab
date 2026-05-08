# Bias And Limitations

## Lookahead Bias

Features must only use information available at or before the signal date. The signal is generated after the close and executed at the next trading day's open.

Rules:

- No random train/test splits.
- No scaler fit on validation or test data.
- No centered rolling windows.
- Labels may look forward, but features may not.
- If future prices are changed, past features and signals must remain unchanged.

## Data Limitations

Milestone 1 uses `yfinance`, which is not a point-in-time institutional data source. Results are useful for software validation, not capital allocation.

Known limitations:

- survivorship bias;
- possible historical revisions;
- missing sessions or throttled downloads;
- no delisted-symbol coverage.

## Execution Limitations

The MVP uses next-open execution with simple slippage and commissions. This is more realistic than same-close entry, but still far from live-market execution.
