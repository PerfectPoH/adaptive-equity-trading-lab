# XMOM Trial 001 Catalyst Classification

## Summary

Manual catalyst classification for all 11 completed trades in `TRIAL-XMOM-001`.

This is a forensic artifact only. It does not change parameters, rerun the strategy, promote the strategy, or authorize paper/live trading.

## Findings

- All 11 trades had at least some observable company-specific narrative before entry.
- 7 of 11 trades had a major issuer event during the holding window.
- The top 3 winners were catalyst-adjacent:
  - CRMD 2025-04-01 -> 2025-05-01: DefenCath/FY2024 commercial rollout evidence and Q1 reporting setup.
  - CRMD 2025-05-01 -> 2025-06-02: preliminary Q1 2025 results and raised H1 sales guidance before entry; formal Q1 results during the trade.
  - AEHR 2025-09-02 -> 2025-10-01: AI processor WLBI evaluation order before entry.
- Catalyst exposure is not sufficient: CRMD 2025-03-03 -> 2025-04-01 and AEHR 2025-10-01 -> 2025-10-30 were large losers despite relevant catalyst context.

## Interpretation

`TRIAL-XMOM-001` is better described as:

```text
catalyst-adjacent momentum exposure on two names
```

not:

```text
distributed cross-sectional momentum edge
```

The evidence supports a future research question, not strategy promotion:

```text
Can a preregistered catalyst-aware momentum rule distinguish continuation from post-catalyst fade?
```

## Decision

```text
NO PAPER TRADING
NO LIVE TRADING
NO MARKOV/HMM PATCH
NO POST-HOC TUNING
NO STRATEGY PROMOTION
```

Next allowed step: write a preregistration spec for a catalyst-aware diagnostic or replication trial, without executing it.
