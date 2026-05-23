# PEAD Alpha Vantage Earnings Probe Gate - 2026-05-23

This gate authorizes one bounded Alpha Vantage `EARNINGS` endpoint probe for `CRMD`.

The probe may inspect only whether the provider exposes fields needed for a future PEAD/SUE data source decision. It does not authorize a backtest, market data download, parameter sweep, paper/live trading, raw payload retention, or strategy promotion.

The probe is valid only if committed before execution.

