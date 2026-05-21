# Earnings Event Extraction Guardrails

Status:

```text
SPEC_ONLY_NOT_EXECUTABLE
```

This document records implementation guardrails for a future earnings-event extractor.

It does not authorize provider queries, OOS execution, parameter sweeps, paper trading, live trading or strategy promotion.

## Narrow Hypothesis

`TRIAL-XMOM-CATALYST-001` stays scoped to earnings-driven catalyst behavior.

Contract:

```text
earnings-only scope
universal anomaly funnel blocked
```

The implementation must not widen the training population to generic FDA, M&A, contract or arbitrary anomaly days just to increase sample size.

## Reaction Session Rule

The event timestamp must be mapped to a first full reaction session before any volume-decay or price-digestion metric is computed.

```text
BMO -> same trading session
AMC -> next trading session
DMT -> purge
UNSPECIFIED -> purge
```

The goal is to compare full regular trading sessions, not mixed partial-session reactions.

## Data Quality Guardrails

The future extractor must monitor:

```text
UNSPECIFIED purge rate
rolling z-score valid observation count
ECDF threshold uncertainty
```

Required policies:

- if `UNSPECIFIED` purge rate exceeds 30%, the spec must be reviewed before execution;
- rolling z-score windows must require at least 45 valid observations out of 60;
- ECDF thresholds must include bootstrap confidence intervals before becoming executable.

## Decision

These guardrails are pre-implementation constraints only.

No extraction script is authorized by this artifact.
