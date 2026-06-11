# Strategy x Regime Router

Date: 2026-06-07

Status: STRATEGY_REGIME_ROUTER_DIAGNOSTIC_ONLY

The dashboard now surfaces a diagnostic Strategy x Market Regime Router. It uses local regime-map artifacts and previously documented failure modes to describe when each strategy family should be blocked, reduced, observed, or used only as a risk overlay.

No provider query was performed. No market-data download was performed. No backtest was performed. Promotion remains disabled.

Purpose:
- Make regime logic visible to the user.
- Explain why momentum, mean reversion, catalysts, dollar bars, ORB, and the risk engine should behave differently across drawdown stress, range, trend, chop, and insufficient-history regimes.
- Prevent the Portfolio Lab from treating every strategy sleeve as equally usable in every market state.

Operating rule:
- BLOCK means no capital or proxy research should be routed through that family in that regime.
- OBSERVE_ONLY means the family can be used as context only.
- REDUCE means smaller sizing and stricter gates would be required before further tests.
- ALLOW_PROXY means local exploration is allowed but remains non-promotable.
- RISK_OVERLAY means the component can govern exposure or measurement quality but is not standalone alpha.

The router is a governance and explanation layer, not a promoted strategy.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
