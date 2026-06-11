# Report Regime Map Diagnostic 001 - 2026-05-24

Decision: `REGIME_MAP_DIAGNOSTIC_COMPLETE_NO_STRATEGY`

## Scope

Existing daily OHLCV and archived trade logs only. No provider query, market-data download, new backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.

## Result

- Regime day count: 5010
- Mapped trade count: 49
- Blockers: none
- Regime counts: {"MIXED_NORMAL": 427, "QUIET_RANGE": 130, "TREND_DOWN": 2096, "TREND_UP": 1603, "VOLATILITY_SHOCK": 754}

## Attribution

- LOWVOL-TRADABILITY-BACKTEST-001 / MIXED_NORMAL: trades=2 net_sum=-0.1306144938 median_net=-0.0653072469 win_rate=0.0
- LOWVOL-TRADABILITY-BACKTEST-001 / QUIET_RANGE: trades=1 net_sum=-0.0185314685 median_net=-0.0185314685 win_rate=0.0
- LOWVOL-TRADABILITY-BACKTEST-001 / TREND_DOWN: trades=27 net_sum=-1.668762948 median_net=-0.0798245614 win_rate=0.185185
- LOWVOL-TRADABILITY-BACKTEST-001 / TREND_UP: trades=13 net_sum=-0.4882852895 median_net=-0.0478165939 win_rate=0.384615
- LOWVOL-TRADABILITY-BACKTEST-001 / VOLATILITY_SHOCK: trades=6 net_sum=-0.6099632618 median_net=-0.1105906383 win_rate=0.166667

## Interpretation

This diagnostic maps archived failures to observable regimes. It does not rescue any strategy; it can only identify whether a future regime-conditioned preregistration is worth writing.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
