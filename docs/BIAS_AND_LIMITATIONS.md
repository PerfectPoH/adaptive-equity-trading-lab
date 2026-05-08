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

## News Feature Limitations

The MVP uses GDELT DOC API macro-news features as broad market context. These features are lagged by one day to reduce lookahead risk, but they are not a substitute for point-in-time financial news feeds, earnings calendars, or company-specific event data.

Current news features should be treated as experimental research inputs, not as an execution trigger.

## Execution Limitations

The MVP uses next-open execution with simple slippage and commissions. This is more realistic than same-close entry, but still far from live-market execution.

`backtesting.py` is used as a prototyping engine. The strategy passes a precomputed next-open entry price as a limit order so the framework validates stop-loss and take-profit levels against the intended entry price, not the previous close. This is a simulation convenience, not a live-order recommendation.

Daily OHLC bars cannot prove the exact intraday order of events. If an entry and its contingent stop/take-profit can interact inside the same daily candle, the result is ambiguous. This is one reason the institutional validation roadmap requires event-driven backtesting before real-money use.

The current conservative MVP skips trades where the entry bar itself touches stop-loss or take-profit levels, reducing ambiguous daily-bar fills at the cost of fewer trades.
