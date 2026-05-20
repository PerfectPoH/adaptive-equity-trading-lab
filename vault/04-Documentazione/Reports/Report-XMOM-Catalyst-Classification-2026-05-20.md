---
tipo: xmom-catalyst-classification
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Catalyst Classification - 2026-05-20

## Scope

Manual catalyst classification for all 11 `TRIAL-XMOM-001` trades.

This report is forensic only. It does not rerun the strategy, change parameters, promote the strategy or authorize paper/live trading.

## Artifact

```text
experiments/runs/xmom_trial_001_20260520/trade_forensics_catalyst_log.csv
experiments/runs/xmom_trial_001_20260520/trade_forensics_catalyst_summary.md
```

## Classification Columns

```text
symbol
signal_date
entry_date
exit_date
pnl
top3_flag
known_catalyst_before_entry
known_catalyst_during_trade
catalyst_type
primary_source_url
secondary_source_url
interpretation
```

## Result

High-level result:

```text
all 11 trades had some observable company-specific narrative before entry
7 of 11 trades had major issuer events during the holding window
top 3 winners were catalyst-adjacent
```

The strongest top-winner case is CRMD 2025-05-01 -> 2025-06-02 because preliminary Q1 results and raised H1 2025 sales guidance were public before entry, and formal Q1 results occurred during the trade.

The AEHR top winner also had an observable ex-ante catalyst: the 2025-08-26 AI-processor wafer-level burn-in evaluation order was public before the 2025-09-02 entry.

## Important Negative Evidence

Catalyst exposure alone is not sufficient:

```text
CRMD 2025-03-03 -> 2025-04-01: -52688.38
AEHR 2025-10-01 -> 2025-10-30: -35910.76
```

Both had relevant catalyst context. This suggests that the unresolved problem is not merely detecting catalysts, but distinguishing:

```text
post-catalyst continuation
vs
post-catalyst fade
```

## Updated Interpretation

`TRIAL-XMOM-001` is not clean evidence of distributed cross-sectional momentum.

Better current description:

```text
catalyst-adjacent momentum exposure on two names
```

This is useful research signal, not a tradable strategy.

## Decision

```text
NO PAPER TRADING
NO LIVE TRADING
NO STRATEGY PROMOTION
NO MARKOV/HMM PATCH
NO POST-HOC PARAMETER TUNING
```

Allowed next work:

- draft a preregistration spec for catalyst-aware momentum diagnostics;
- define static catalyst taxonomy and observable-before-entry rules;
- build a source hierarchy for manual/automated event evidence;
- do not execute any new trial until the spec is frozen.

Sources used:

- CorMedix preliminary Q4 2024: https://cormedix.com/cormedix-inc-announces-preliminary-fourth-quarter-2024-results-and-provides-business-update/
- CorMedix FY2024 results: https://cormedix.com/cormedix-inc-reports-fourth-quarter-and-full-year-2024-financial-results-and-provides-business-update/
- CorMedix preliminary Q1 2025 / H1 guidance raise: https://cormedix.com/cormedix-inc-announces-preliminary-first-quarter-2025-results-and-raises-h1-2025-net-sales-guidance/
- CorMedix Q1 2025 results: https://cormedix.com/cormedix-inc-reports-first-quarter-2025-financial-results-and-provides-business-update/
- CorMedix LDO implementation: https://cormedix.com/cormedix-inc-announces-customer-implementation/
- CorMedix Q2 2025 results: https://cormedix.com/cormedix-inc-reports-second-quarter-2025-financial-results-and-provides-business-update/
- CorMedix Melinta acquisition: https://cormedix.com/cormedix-to-acquire-melinta-therapeutics-creating-diversified-specialty-company-with-strong-presence-in-acute-care-settings/
- Aehr AI WLBI evaluation order: https://www.aehr.com/2025/08/aehr-test-systems-announces-wafer-level-burn-in-and-test-application-evaluation-order-from-leading-ai-processor-supplier/
- Aehr Q1 FY2026 earnings date: https://www.aehr.com/2025/09/aehr-test-systems-to-announce-first-quarter-fiscal-2026-financial-results-on-october-6-2025/
- Aehr Q1 FY2026 results: https://www.aehr.com/2025/10/aehr-test-systems-reports-fiscal-2026-first-quarter-financial-results/

See [[Report-XMOM-Trial-001-Forensic-Interpretation-2026-05-20]].
