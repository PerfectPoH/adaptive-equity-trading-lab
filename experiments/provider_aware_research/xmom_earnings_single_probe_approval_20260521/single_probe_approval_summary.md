# XMOM Earnings Single Probe Approval - 2026-05-21

Status:

```text
SPEC_ONLY_AWAITING_SEPARATE_APPROVAL
```

This artifact defines a future one-provider, one-symbol probe for earnings-calendar/report-time metadata.

It does not authorize the probe.

## Scope

Allowed only after separate explicit approval:

```text
one provider
one symbol
one endpoint
one provider call
derived/redacted output only
```

Still blocked:

```text
provider query
price-volume data
raw payload retention
extractor implementation
OOS execution
paper/live trading
strategy promotion
```

## Purpose

The probe exists only to answer:

```text
Does the candidate provider expose enough historical earnings report-time metadata to support BMO/AMC/DMT/UNSPECIFIED quality checks?
```
