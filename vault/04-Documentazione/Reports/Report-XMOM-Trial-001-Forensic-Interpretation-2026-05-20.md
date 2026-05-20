---
tipo: xmom-forensic-interpretation
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Trial 001 Forensic Interpretation - 2026-05-20

## Scope

Independent forensic interpretation of the already completed `TRIAL-XMOM-001`.

This report does not change parameters, does not rerun the strategy, does not promote the strategy and does not authorize paper/live trading.

## Artifacts

Generated in:

```text
experiments/runs/xmom_trial_001_20260520/
```

Files:

```text
trade_forensics_report.json
trade_forensics_report.md
trade_forensics_top_trades.csv
trade_forensics_non_top_trades.csv
```

Analyzer:

```text
src/experiments/xmom_trial_forensic_analyzer.py
```

## Forensic Summary

```text
total_trades: 11
winner_count: 5
loser_count: 6
total_pnl: +109363.25
top_3_pnl: +159448.57
rest_pnl: -50085.32
top_3_contribution_pct: 145.80%
sign_flip_excluding_top_3: true
```

Top 3 trades:

```text
AEHR 2025-09-02 -> 2025-10-01: +66657.14
CRMD 2025-05-01 -> 2025-06-02: +46861.70
CRMD 2025-04-01 -> 2025-05-01: +45929.73
```

Symbol concentration:

```text
CRMD: 8 trades, +90469.56 total P&L
AEHR: 3 trades, +18893.69 total P&L
```

## Public Catalyst Notes

Initial source checks suggest the top winners were likely near company-specific catalysts, not generic cross-sectional momentum alone.

CRMD:

- CorMedix announced preliminary Q1 2025 results and raised first-half 2025 net sales guidance in April 2025.
- CorMedix reported Q1 2025 net revenue of $39.1 million on May 6, 2025, with profitability and DefenCath commercial rollout details.
- The two CRMD top trades span 2025-04-01 to 2025-05-01 and 2025-05-01 to 2025-06-02, overlapping this catalyst window.

AEHR:

- Aehr announced an AI-processor wafer-level burn-in evaluation order on 2025-08-26.
- The AEHR top trade enters 2025-09-02 and exits 2025-10-01, shortly after that catalyst.
- Aehr later reported fiscal Q1 2026 results on 2025-10-06, after this trade window.

Sources:

```text
https://cormedix.com/cormedix-inc-announces-preliminary-first-quarter-2025-results-and-raises-h1-2025-net-sales-guidance/
https://cormedix.com/cormedix-inc-reports-first-quarter-2025-financial-results-and-provides-business-update/
https://www.aehr.com/2025/08/aehr-test-systems-announces-wafer-level-burn-in-and-test-application-evaluation-order-from-leading-ai-processor-supplier/
https://www.aehr.com/2025/10/aehr-test-systems-reports-fiscal-2026-first-quarter-financial-results/
```

## Interpretation

The evidence does not support immediate Markov/HMM integration or post-hoc regime filtering.

The stronger interpretation is:

```text
XMOM-001 may be selecting stocks that already have strong catalyst-driven repricing,
but the current portfolio is too concentrated and too sample-small to distinguish edge from lucky catalyst exposure.
```

This suggests the next research object should be `catalyst-aware momentum forensics`, not a new execution trial.

## Decision

```text
NO PAPER TRADING
NO LIVE TRADING
NO STRATEGY PROMOTION
NO MARKOV FILTER PATCHING
NO POST-HOC PARAMETER TUNING
```

Allowed next work:

- build a catalyst classification note for the 11 trades;
- compare top 3 vs non-top 8 trade features;
- inspect whether CRMD/AEHR catalysts were observable before entry;
- design a future preregistered replication trial only after the forensic interpretation is complete.

Blocked:

- using Markov/HMM to rescue this result after seeing the outlier failure;
- treating the CRMD/AEHR catalyst windows as proof of general XMOM edge;
- launching paper trading from `TRIAL-XMOM-001`.

See [[Report-XMOM-Trial-001-Execution-2026-05-20]] and [[Project-Handoff]].
