# Regime Switching Portfolio Diagnostic

Date: 2026-06-07

Status: REGIME_SWITCHING_PORTFOLIO_DIAGNOSTIC_ONLY

Portfolio Lab now includes a dynamic regime-switching diagnostic. Instead of building only one basket for the current regime, it replays the local/proxy component return streams through time and changes eligible strategy sleeves whenever the local regime map changes.

No provider query was performed. No market-data download was performed. No true backtest was performed. Promotion remains disabled.

Method:
- Build local component return streams from saved Workbench/factory artifacts.
- Infer the active regime for each period from the local regime map using date-aware majority labels.
- Apply the Strategy x Regime Router before reading that period's component returns.
- Exclude BLOCK and OBSERVE_ONLY sleeves.
- Normalize weights across allowed components using fixed posture multipliers.
- Compare the dynamic path against a static equal-weight basket on the same component set.

Current local/proxy result:
- dynamic_total_net_return: `31.28991359`
- static_total_net_return: `39.92538976`
- dynamic_vs_static_delta: `-8.63547617`
- dynamic_max_drawdown: `-8.21040412`
- static_max_drawdown: `-4.5973971`
- period_count: `2015`
- component_count: `108`

Interpretation:

The first dynamic regime-switching diagnostic did not outperform the static proxy basket. This is not a failure of the architecture; it is evidence that the current regime rules are defensive governance diagnostics, not yet proven return-enhancement logic.

Anti-overfit rule:

The regime switch is applied before period returns are read. The diagnostic does not tune regime rules to maximize the historical curve and cannot promote a strategy.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
