---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-21
agente: codex
tags: [earnings, timestamp, classifier, bmo, amc, dmt, no-query]
---

# 2026-05-21 - Earnings Timestamp Classifier

## Contesto

After recording the Intrinio/CRMD theoretical review, the next safe implementation step was a provider-agnostic timestamp classifier.

## Cosa e' cambiato

Added:

```text
src/validation/earnings_timestamp_classifier.py
tests/test_earnings_timestamp_classifier.py
experiments/validation/earnings_timestamp_classifier_20260521/
```

## Verifiche

Targeted tests:

```text
8 passed
```

Classifier policy:

```text
missing/date-only/midnight/invalid -> UNSPECIFIED -> purge
local time < 09:30 America/New_York -> BMO
09:30 <= local time < 16:00 America/New_York -> DMT -> purge
local time >= 16:00 America/New_York -> AMC
```

## Decisione

The classifier is a local deterministic utility only.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion occurred.

See [[Report-Earnings-Timestamp-Classifier-2026-05-21]].
