# Norgate Portfolio Trial Backtest Gate 001

This gate authorizes one bounded, trial-limited Portfolio Candidate 002 diagnostic backtest using the locally installed Norgate Data trial.

The run is allowed only after `NORGATE-DATA-PROBE-001` confirmed Python access, US active equities, US delisted equities, adjusted daily prices, and quote-date metadata.

The run may not optimize parameters, search component combinations, promote a strategy, paper trade, live trade, or make a durable financial performance claim. The result must remain trial-limited because the free trial history is expected to cover only roughly two years.

The frozen portfolio component grammar is inherited from Portfolio Candidate 002:

- Catalyst: disabled unless point-in-time event timestamps and direction source exist.
- Dollar-Bar Microstructure: disabled unless intraday/tick reconstruction exists.
- Mean Reversion: fixed daily OHLCV proxy sleeve.
- Momentum: fixed daily OHLCV proxy sleeve.

Disabled sleeves keep their weight idle; weights are not redistributed after seeing results.
