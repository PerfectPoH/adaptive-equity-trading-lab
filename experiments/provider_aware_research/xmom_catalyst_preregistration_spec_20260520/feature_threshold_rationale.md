# Feature Threshold Rationale - TRIAL-XMOM-CATALYST-001

Status:

```text
THEORY_REVIEW_ONLY_NOT_EXECUTABLE
```

This artifact records literature/logic guidance for future catalyst-aware features. It does not finalize thresholds, authorize execution, or modify `TRIAL-XMOM-001`.

## Research Premise

The manual catalyst classification showed that catalyst exposure alone is not an edge. Both winners and losers were catalyst-adjacent.

The next hypothesis is therefore not:

```text
buy catalyst stocks
```

but:

```text
distinguish post-catalyst continuation from post-catalyst fade before entry
```

## Literature Signals Used

### PEAD and delayed reaction

Post-earnings announcement drift literature supports the idea that markets may underreact to earnings/news and drift in the direction of the surprise after announcement.

Operational implication:

```text
Do not enter on catalyst presence alone.
Require evidence that the market has not fully digested the information and that continuation is still plausible.
```

### Investor attention and volume

Investor attention papers suggest that pre-announcement attention and abnormal trading volume affect how much drift remains after the announcement.

Operational implication:

```text
Volume persistence/decay should be diagnostic.
High one-day attention followed by rapid volume collapse is fade risk.
Persistent volume after catalyst is a possible continuation condition.
```

### Liquidity and implementation cost

PEAD and momentum interact with liquidity and adverse selection costs. Small-cap signals can be eaten by liquidity/impact costs.

Operational implication:

```text
Do not separate continuation logic from liquidity and participation guardrails.
Keep square-root impact and participation caps in the trial.
```

## Feature Logic

### Catalyst Lag

Purpose:

```text
Avoid same-day catalyst chaos and stale catalyst attribution.
```

Logic:

- Too short: entry may chase event-day microstructure, gap, spread and first-day attention.
- Too long: attribution becomes weak and later price action may no longer be catalyst-related.

Candidate policy:

```text
candidate_lag_min: proposed_not_final
candidate_lag_max: proposed_not_final
```

No numeric threshold is executable yet.

### Volume Persistence / Decay

Purpose:

```text
Separate sustained institutional/market absorption from one-day attention spike.
```

Continuation intuition:

```text
volume remains above pre-catalyst ADV while price holds or consolidates
```

Fade intuition:

```text
volume collapses quickly after catalyst while price loses the catalyst reference
```

Candidate metrics:

```text
volume_persistence_ratio_3d
volume_persistence_ratio_5d
volume_decay_ratio
```

No numeric threshold is executable yet.

### Price Digestion

Purpose:

```text
Avoid buying exhausted post-catalyst spikes that have already failed.
```

Continuation intuition:

```text
price holds above catalyst-day or first-post-catalyst reference
```

Fade intuition:

```text
price retraces materially from post-catalyst high before signal
```

Candidate metrics:

```text
price_digestion_hold_ratio
post_catalyst_max_retrace_pct
gap_hold_flag
```

No numeric threshold is executable yet.

## Forbidden Threshold Selection

The following remains blocked:

```text
select thresholds from CRMD/AEHR winners
select thresholds from TRIAL-XMOM-001 PnL
select thresholds by maximizing the old run result
retroactively label catalyst winners as proof of edge
```

Any future threshold must come from:

- a separate literature/logic review;
- a broader independent sample;
- a new preregistration update before execution.

## Sources

- Bernard and Thomas PEAD literature is referenced in later PEAD reviews and earnings drift work.
- DellaVigna and Pollet, "Investor Inattention, Firm Reaction, and Friday Earnings Announcements", NBER Working Paper 11683: https://www.nber.org/papers/w11683
- Frazzini and Lamont, "The Earnings Announcement Premium and Trading Volume", NBER Working Paper 13090: https://www.nber.org/papers/w13090
- Wang, Choi and Siraj, "Local Investor Attention and Post-Earnings Announcement Drift", Review of Quantitative Finance and Accounting: https://epublications.marquette.edu/fin_fac/161/
- Ayers, Li and Yeung, "Investor Trading and the Post Earnings Announcement Drift", The Accounting Review: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1270811
- Sadka, "Momentum and post-earnings-announcement drift anomalies: The role of liquidity risk", Journal of Financial Economics: https://ideas.repec.org/a/eee/jfinec/v80y2006i2p309-349.html

## Decision

This rationale supports future spec refinement only.

It does not make `TRIAL-XMOM-CATALYST-001` executable.
