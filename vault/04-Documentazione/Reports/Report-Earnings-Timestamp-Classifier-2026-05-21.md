---
tipo: earnings-timestamp-classifier
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: VALIDATED_NO_PROVIDER_QUERY
---

# Report Earnings Timestamp Classifier - 2026-05-21

## Scope

Added a local deterministic utility for mapping earnings timestamp fields to reaction-session classifications.

Module:

```text
src/validation/earnings_timestamp_classifier.py
tests/test_earnings_timestamp_classifier.py
```

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Policy

```text
missing/date-only/midnight/invalid -> UNSPECIFIED -> purge
local time < 09:30 America/New_York -> BMO -> allow_candidate, same_regular_session
09:30 <= local time < 16:00 America/New_York -> DMT -> purge
local time >= 16:00 America/New_York -> AMC -> allow_candidate, next_regular_session
```

The classifier uses timezone-aware conversion to `America/New_York`, including DST handling through the Python standard library `zoneinfo`.

## Validation

Artifact:

```text
experiments/validation/earnings_timestamp_classifier_20260521/earnings_timestamp_classifier_validation_report.json
experiments/validation/earnings_timestamp_classifier_20260521/README.md
```

Targeted tests:

```text
8 passed
```

Covered cases:

```text
missing input
date-only timestamp
midnight timestamp
BMO summer/DST
DMT open boundary
AMC close boundary
winter EST conversion
timezone-aware datetime input
malformed timestamp
```

## Decision

The timestamp classifier is validated as a local policy utility.

It does not authorize the Intrinio/CRMD probe and does not implement a provider extractor.

See [[Report-XMOM-Earnings-Single-Probe-Theoretical-Review-2026-05-21]].
