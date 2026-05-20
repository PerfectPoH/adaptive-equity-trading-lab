---
tipo: xmom-catalyst-feature-rationale
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: THEORY_REVIEW_ONLY_NOT_EXECUTABLE
---

# Report XMOM Catalyst Feature Rationale - 2026-05-20

## Scope

Created a theory/logic review for future `TRIAL-XMOM-CATALYST-001` feature thresholds.

No execution, provider query, backtest, sweep, paper trading, live trading, Markov/HMM patch or strategy promotion was performed.

## New Artifacts

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/feature_threshold_rationale.md
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/threshold_candidate_policy.csv
```

## Rationale

The literature supports studying post-event drift, but not catalyst presence alone.

Useful families:

```text
catalyst_lag
volume_persistence / volume_decay
price_digestion
liquidity and participation constraints
```

The core interpretation remains:

```text
Catalyst exposure != edge
Continuation/fade discrimination is the actual research question.
```

## Threshold Policy

All actionable thresholds remain:

```text
not_final
not_executable
TBD
```

This is deliberate. Thresholds must not be selected from:

```text
TRIAL-XMOM-001 PnL
CRMD/AEHR winner anatomy
old outlier pattern
```

The only locked thresholds are governance thresholds:

```text
minimum_accepted_trades_for_promotion = 30
top3_contribution_promotion_cap = 100%
```

## Sources Reviewed

- DellaVigna and Pollet, "Investor Inattention, Firm Reaction, and Friday Earnings Announcements", NBER Working Paper 11683: https://www.nber.org/papers/w11683
- Frazzini and Lamont, "The Earnings Announcement Premium and Trading Volume", NBER Working Paper 13090: https://www.nber.org/papers/w13090
- Wang, Choi and Siraj, "Local Investor Attention and Post-Earnings Announcement Drift", Review of Quantitative Finance and Accounting: https://epublications.marquette.edu/fin_fac/161/
- Ayers, Li and Yeung, "Investor Trading and the Post Earnings Announcement Drift", The Accounting Review: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1270811
- Sadka, "Momentum and post-earnings-announcement drift anomalies: The role of liquidity risk", Journal of Financial Economics: https://ideas.repec.org/a/eee/jfinec/v80y2006i2p309-349.html

## Decision

The spec remains valid but not executable.

Validator update completed:

```text
SPEC_VALIDATION_PASS
passed: 58
failed: 0
```

The rationale artifacts are now part of the structural contract.

Next allowed work:

- create an implementation gate spec if the user explicitly approves;
- design independent threshold selection;
- still no trial execution.

See [[Report-XMOM-Catalyst-Preregistration-Validator-2026-05-20]].
