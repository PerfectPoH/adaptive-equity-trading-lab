# Bias And Limitations

## Lookahead Bias

Features must only use information available at or before the signal date. The signal is generated after the close and executed at the next trading day's open.

Rules:

- No random train/test splits.
- No scaler fit on validation or test data.
- No centered rolling windows.
- Labels may look forward inside their own period, but rows whose label horizon crosses a train/validation/test boundary must be purged.
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

## Probability Calibration Limitations

The raw Random Forest output is not a literal success probability. Calibration diagnostics show meaningful gaps between predicted probability bins and observed TP-before-SL success rates.

The current research default uses isotonic calibration fit on validation only, but it is still a prototype calibration layer. It improved the 2024 backtest, but it must be rechecked with broader walk-forward folds and better data before any live use.

## Execution Limitations

The MVP uses next-open execution with simple slippage and commissions. This is more realistic than same-close entry, but still far from live-market execution.

`backtesting.py` is used as a prototyping engine. The strategy passes a precomputed next-open entry price as a limit order so the framework validates stop-loss and take-profit levels against the intended entry price, not the previous close. This is a simulation convenience, not a live-order recommendation.

Daily OHLC bars cannot prove the exact intraday order of events. If an entry and its contingent stop/take-profit can interact inside the same daily candle, the result is ambiguous. This is one reason the institutional validation roadmap requires event-driven backtesting before real-money use.

The current conservative MVP skips trades where the entry bar itself touches stop-loss or take-profit levels, reducing ambiguous daily-bar fills at the cost of fewer trades.
