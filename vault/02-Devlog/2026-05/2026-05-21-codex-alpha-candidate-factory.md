# Report Alpha Candidate Factory - 2026-05-21

Decision: `ALPHA_CANDIDATE_FACTORY_READY_NO_EXECUTION`

## Purpose

The lab has strong falsification infrastructure but no validated profitable strategy. This factory creates a ranked queue of small, falsifiable candidates without authorizing execution.

## Top Candidates

- ALPHA-009 (82): best_diagnostic_probe - Outlier-resistant cross-sectional ranking using median trade contribution, not total PnL.
- ALPHA-003 (78): best_infrastructure_probe - Dollar-bar version of opening reclaim reduces time-bar noise before strategy logic.
- ALPHA-010 (76): best_governance_integration - Cooldown and BAD_WIN exclusion improve live survivability but do not create alpha.
- ALPHA-008 (73): meta_infrastructure_probe - Provider sensitivity arbitrage is not alpha but can identify data-fragile hypotheses early.
- ALPHA-007 (71): research_filter_probe - Same-day bad-news fade avoidance: no long reversion if SEC event is fundamental break.

## Guardrails

- No provider query.
- No backtest.
- No threshold selection from old PnL.
- No paper/live trading.
- Every candidate declares its primary failure mode before any future probe.

Next safe step: Implement diagnostic-only outlier-resistant candidate ranking harness on existing artifacts.
