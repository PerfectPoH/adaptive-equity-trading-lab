# Dynamic Regime-Switching Trial Dry-Run

Date: 2026-06-07

Status: DYNAMIC_REGIME_SWITCHING_TRIAL_DRY_RUN_COMPLETE

The separate Portfolio Lab trial pipeline now understands `dynamic_regime_switching` pre-registration drafts.

No provider query was performed. No market-data download was performed. No true backtest was performed. Promotion remains disabled.

Behavior:
- Static drafts continue to run through the existing separate portfolio diagnostic.
- Dynamic drafts replay the frozen regime-switching contract through `build_regime_switching_portfolio_diagnostic`.
- The trial stores `candidate_type`, `regime_switching_contract`, `regime_switching_diagnostic`, and a dynamic-specific final decision.
- If the dynamic path underperforms the static proxy baseline, the final decision carries `dynamic_underperformed_static_proxy`.
- The external data contract blocker remains present before any stronger claim.

UI change:
- Portfolio Lab now lets the user choose `Static Portfolio Candidate` or `Dynamic Regime-Switching Candidate` before creating the pre-registration draft.
- Approved dynamic drafts can run a separate dynamic dry-run without being routed through the static frozen-recipe validation path.

Interpretation:

The project now has the full governed lifecycle for a dynamic multi-regime idea: diagnostic, draft, approval gate, and separate dry-run. It is still proxy-only and non-promotable until a true survivorship-free/PIT data bundle exists.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
