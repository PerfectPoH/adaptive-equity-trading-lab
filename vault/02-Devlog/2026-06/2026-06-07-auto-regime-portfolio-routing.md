# Auto Regime Portfolio Routing

Date: 2026-06-07

Status: CURRENT_REGIME_INFERRED_FROM_LOCAL_MAP

Portfolio Lab now defaults the active market regime from the latest local large-cap/ETF regime map before running the regime-aware component filter.

No provider query was performed. No market-data download was performed. No true backtest was performed. Promotion remains disabled.

Inference rule:
- Use the latest available date in the local regime map.
- Count regime labels across symbols on that date.
- Select the majority label as the default active regime.
- Report confidence as majority_count / symbol_count.
- Keep manual override available in the UI.

Current local inference:
- regime: `TREND_UP_LOW_VOL`
- as_of_date: `2026-05-08`
- confidence: `40%`
- symbol_count: `10`

Anti-overfit rule:

The regime is inferred before the portfolio diagnostic and is not selected from portfolio returns. The router can block, reduce, or allow strategy families by market state, but it cannot promote a strategy or claim live readiness.

Interpretation:

This is the first step from "user manually chooses the market moment" toward an automatic Regime-Aware Strategy Engine.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
