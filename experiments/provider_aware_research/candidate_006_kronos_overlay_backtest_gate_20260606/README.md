# Candidate 006 Kronos Overlay Backtest Gate 001

This gate authorizes one diagnostic overlay backtest.

The frozen rule is simple and non-optimized: keep an existing Candidate 005 long trade only if `kronos_forecast_return_median > 0`; otherwise route that trade weight to cash. Rejected weight is not redistributed.

No new inference, provider query, market-data download, threshold sweep, reranking, fine-tuning, paper trading, live trading, or promotion is allowed.
