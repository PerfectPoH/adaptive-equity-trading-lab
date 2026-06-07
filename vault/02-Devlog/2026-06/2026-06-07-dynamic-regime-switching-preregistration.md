# Dynamic Regime-Switching Pre-Registration Draft

Date: 2026-06-07

Status: DYNAMIC_REGIME_SWITCHING_DRAFT_REQUIRES_MANUAL_APPROVAL

Portfolio Lab can now create two pre-registration draft types:
- `static_portfolio`
- `dynamic_regime_switching`

No provider query was performed. No market-data download was performed. No true backtest was performed. Promotion remains disabled.

Dynamic draft contract:
- active regime is read before portfolio returns are evaluated;
- BLOCK and OBSERVE_ONLY sleeves are excluded;
- REDUCE, ALLOW_PROXY, and RISK_OVERLAY sleeves may enter;
- fallback is cash when no component is allowed;
- rebalance happens on regime change or period boundary;
- weights are normalized from frozen posture multipliers;
- optimization is not allowed.

Additional falsification criteria:
- archive if dynamic regime switching underperforms the static baseline under true data;
- archive if any regime has too few independent periods;
- archive if regime routing is tuned after seeing returns.

Current proxy disclosure:

The local/proxy dynamic diagnostic underperformed the static equal basket, so dynamic drafts include `dynamic_underperformed_static_proxy` in their anti-overfit disclosures when created from this state.
