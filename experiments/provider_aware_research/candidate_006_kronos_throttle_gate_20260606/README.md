# Candidate 006 Kronos Throttle Gate 001

This gate authorizes one diagnostic only: apply a fixed half-size throttle to archived Candidate 006 trades.

Trades with `kronos_forecast_return_median > 0` keep full weight. Trades with `kronos_forecast_return_median <= 0` keep half weight instead of being fully removed.

No new Kronos inference, provider query, market-data download, threshold sweep, multiplier sweep, reranking, weight redistribution, promotion, paper trading, or live trading is allowed.
