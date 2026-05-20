# TRIAL-XMOM-CATALYST-001 Preregistration Spec

Status:

```text
SPEC_ONLY_NOT_EXECUTED
```

This directory freezes the next research hypothesis after the `TRIAL-XMOM-001` catalyst forensics.

No backtest, sweep, provider query, paper trading, live trading, strategy promotion, parameter tuning or Markov/HMM patching is authorized by this spec.

## Research Question

```text
Can a preregistered catalyst-aware momentum rule distinguish post-catalyst continuation from post-catalyst fade before entry?
```

## Motivation

`TRIAL-XMOM-001` had a positive headline return, but failed outlier stress. Manual catalyst classification showed:

```text
11/11 trades had observable company-specific narrative before entry
7/11 trades had major issuer events during the holding window
top 3 winners were catalyst-adjacent
large losers also had catalyst context
```

Therefore, the unresolved problem is not simply catalyst detection. The unresolved problem is distinguishing continuation from fade.

## Frozen Philosophy

```text
Catalyst exposure != edge
Continuation/fade discrimination must be observable before entry
No post-hoc parameter rescue from TRIAL-XMOM-001
No Markov/HMM regime patch in this trial
No strategy promotion without a separate promotion gate
```

## Artifact Files

```text
hypothesis.md
catalyst_taxonomy.csv
allowed_features.csv
parameter_freeze.csv
decision_rule.csv
blocked_actions.csv
source_hierarchy.csv
```

## Execution Status

This is a documentation/preregistration artifact only.

The trial is not implemented and not executable.
