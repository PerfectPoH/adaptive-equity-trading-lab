# Hypothesis - TRIAL-XMOM-CATALYST-001

## Trial ID

```text
TRIAL-XMOM-CATALYST-001
```

## Preregistration ID

```text
PREREG-XMOM-CATALYST-001
```

## Status

```text
SPEC_ONLY_NOT_EXECUTED
```

## Null Hypothesis

Adding catalyst-aware ex-ante filters to XMOM does not improve out-of-sample robustness versus the frozen `TRIAL-XMOM-001` structure after accounting for market impact, outlier concentration and benchmark comparison.

## Research Hypothesis

For small-cap names with observable company-specific catalysts, post-catalyst continuation can be distinguished from post-catalyst fade using only information available before entry:

```text
catalyst lag
volume persistence / decay
price digestion
```

## Expected Mechanism

Continuation candidates should show:

- catalyst known before entry;
- enough time after the catalyst to avoid first-day microstructure noise;
- persistent above-average volume after the catalyst;
- price holding above a catalyst-day reference level or consolidating without full retracement.

Fade candidates should show:

- rapid volume decay after catalyst;
- price retracing below catalyst-day reference levels;
- entry too close to event-day volatility;
- exhausted price move after a sharp news spike.

## Forbidden Inference

The trial must not infer:

- that catalyst presence alone is bullish;
- that `TRIAL-XMOM-001` positive headline P&L is a validated edge;
- that Markov/HMM regime filtering can rescue this trial;
- that CRMD/AEHR top winners prove a generalizable rule.

## Required Output If Implemented Later

Any future execution must produce:

- catalyst candidate log;
- feature table with all values calculated before entry;
- accepted/rejected candidates with reasons;
- benchmark report;
- portfolio trade log;
- outlier diagnostics;
- post-run validation report;
- explicit decision against promotion unless all robustness gates pass.
