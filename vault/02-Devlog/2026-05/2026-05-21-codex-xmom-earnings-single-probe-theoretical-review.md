---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-21
agente: codex
tags: [xmom, earnings, provider, review, intrinio, crmd, no-query]
---

# 2026-05-21 - XMOM Earnings Single Probe Theoretical Review

## Contesto

After deciding not to proceed to live approval, the safe next step was recording the theoretical provider/symbol review as a non-executable artifact.

## Cosa e' cambiato

Added:

```text
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/
src/experiments/xmom_earnings_single_probe_theoretical_review_validator.py
tests/test_xmom_earnings_single_probe_theoretical_review_validator.py
```

Selected theoretical candidates:

```text
provider_candidate=Intrinio
symbol_candidate=CRMD
timestamp_field_candidate=expected_8k_at
```

## Verifiche

Targeted tests:

```text
7 passed
```

Review validator:

```text
XMOM_EARNINGS_SINGLE_PROBE_THEORETICAL_REVIEW_PASS
33/33 checks passed
approval_granted=false
provider_query_performed=false
```

Live state checks:

```text
live approval directory exists: false
single-probe output directory exists: false
single-probe ledger exists: false
```

## Decisione

The theoretical review is valid but does not authorize execution.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion occurred.

See [[Report-XMOM-Earnings-Single-Probe-Theoretical-Review-2026-05-21]].
