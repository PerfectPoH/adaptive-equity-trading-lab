# Candidate 004 Regime-Routed Backtest Postmortem 001

Decision: `CANDIDATE_004_ARCHIVE_CURRENT_FORM_RESEARCH_LEAD_ONLY`

Scope: review only. No additional backtest, no parameter sweep, no promotion.

## What Improved

- The router did what it was supposed to do mechanically: all trades came from `RECOVERY_BOUNCE`.
- Win rate improved to `0.571` and max drawdown compressed to `-0.027512`.

## Why It Still Failed

- Total trades fell to `14`, triggering sample starvation.
- Best symbol `FCEL` carried the whole result; ex-best-symbol net was `-0.000692`.
- Benchmark-relative net was negative versus IWM `-0.293528` and SPY `-0.321741`.

## Interpretation

Candidate 004 is a better risk router than Candidate 003, but not a promotable alpha strategy. The architecture should be preserved as a risk-control idea, not capital deployment.

## Next Allowed Action

`design_candidate_005_oos_or_long_history_regime_router_only_after_data_upgrade`
