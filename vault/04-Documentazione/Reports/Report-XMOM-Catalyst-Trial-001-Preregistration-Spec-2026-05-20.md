---
tipo: xmom-catalyst-preregistration
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: SPEC_ONLY_NOT_EXECUTED
---

# Report XMOM Catalyst Trial 001 Preregistration Spec - 2026-05-20

## Scope

Created a spec-only preregistration for:

```text
TRIAL-XMOM-CATALYST-001
PREREG-XMOM-CATALYST-001
```

This is not an execution. No backtest, provider query, sweep, paper trading, live trading, Markov/HMM patch or strategy promotion was performed.

## Research Question

```text
Can a preregistered catalyst-aware momentum rule distinguish post-catalyst continuation from post-catalyst fade before entry?
```

## Motivation

`TRIAL-XMOM-001` showed:

```text
positive headline P&L
outlier stress failure
100% catalyst/narrative exposure across 11 trades
large winners and large losers both catalyst-adjacent
```

Therefore:

```text
Catalyst exposure != edge
```

The next valid research target is not "add news" and not "add Markov". It is a frozen testable framework for distinguishing continuation from fade.

## Spec Directory

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/
```

Files:

```text
README.md
hypothesis.md
catalyst_taxonomy.csv
allowed_features.csv
parameter_freeze.csv
decision_rule.csv
blocked_actions.csv
source_hierarchy.csv
```

## Frozen Feature Families

Allowed ex-ante feature families:

```text
catalyst_known_before_entry
catalyst_lag_trading_days
volume_persistence_ratio_3d
volume_persistence_ratio_5d
volume_decay_ratio
price_digestion_hold_ratio
post_catalyst_max_retrace_pct
gap_hold_flag
xmom_rank_aggregate_score
rolling_volatility_20d
avg_dollar_volume_20d
```

Important rule:

```text
All catalyst and feature information must be observable before entry.
```

## Catalyst Taxonomy

Frozen initial taxonomy:

```text
earnings_results
guidance_preliminary_results
commercial_rollout
contract_order
m_and_a
offering_dilution
regulatory_fda
analyst_action
earnings_calendar
no_obvious_catalyst
```

Regulatory/FDA events are explicitly separated from commercial rollout and revenue-inflection events.

## Decision Rules

Primary proposed metric:

```text
excess_return_vs_iwm_net_of_costs_after_catalyst_filters
```

Robustness gate:

```text
No promotion if sign_flip_excluding_top_3 is true
or if top_3 contribution exceeds 100% of total PnL.
```

Sample-size gate:

```text
No promotion if accepted trade count is below 30,
unless the report explicitly labels the result as exploratory only.
```

Promotion rule:

```text
blocked
```

No paper/live trading can be authorized from this spec or a single future run.

## Blocked Actions

```text
execute_backtest
run_parameter_sweep
change_xmom_001_results
markov_hmm_patch
paper_trading
live_trading
strategy_promotion
use_future_news
select_thresholds_from_xmom_001_pnl
merge_fda_with_commercial_rollout
```

## Ledger

Added prepared-not-executed ledger row:

```text
TRIAL-XMOM-CATALYST-001 ... prepared_not_executed ... pending_spec_review
```

## Decision

This spec is approved as a research artifact only.

Next allowed work:

- validate the spec files structurally;
- optionally implement a validator for the preregistration package;
- do not execute the trial until implementation, data, source timestamping and explicit authorization gates are created.

See [[Report-XMOM-Catalyst-Classification-2026-05-20]] and [[Project-Handoff]].
