# Regime-Aware Portfolio Lab

Date: 2026-06-07

Status: REGIME_AWARE_COMPONENT_FILTER_COMPLETE

Portfolio Lab now applies the Strategy x Market Regime Router before running its local/proxy portfolio diagnostic.

No provider query was performed. No market-data download was performed. No true backtest was performed. Promotion remains disabled.

Behavior:
- The user can select an active market regime.
- Components mapped to BLOCK or OBSERVE_ONLY are excluded from the diagnostic basket for that regime.
- Components mapped to REDUCE, ALLOW_PROXY, or RISK_OVERLAY may enter the local/proxy diagnostic.
- The filter contract is shown in the UI and embedded into saved previews when active.

Anti-overfit rule:

The regime filter is not optimized from the portfolio result. It is a pre-diagnostic governance layer derived from documented strategy failure modes and local regime labels. Its purpose is to stop incompatible strategy sleeves from entering a basket, not to search for a better historical equity curve.

Interpretation:

This moves the lab from "best strategy in general" toward "which strategy family is even allowed in this market state," while preserving the existing no-promotion governance.
