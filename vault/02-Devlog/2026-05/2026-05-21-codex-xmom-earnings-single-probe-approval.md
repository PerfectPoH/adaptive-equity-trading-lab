---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-21
agente: codex
tags: [xmom, earnings, provider, probe, gate, no-query]
---

# 2026-05-21 - XMOM Earnings Single Probe Approval

## Contesto

After the earnings provider-selection gate, the next safe step was to define a future one-provider, one-symbol metadata probe without executing it.

The purpose is to test only whether a candidate earnings-calendar provider can expose historical report-time quality fields needed for BMO/AMC/DMT/UNSPECIFIED handling.

## Cosa e' cambiato

Added spec artifact:

```text
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/
```

Added validator:

```text
src/experiments/xmom_earnings_single_probe_approval_validator.py
tests/test_xmom_earnings_single_probe_approval_validator.py
```

Generated validation report:

```text
experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/single_probe_approval_validation_report.json
```

## Verifiche

Targeted tests:

```text
8 passed
```

Validation report:

```text
EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_PASS
38/38 checks passed
```

## Decisione

The artifact is valid but non-executable.

Still blocked:

```text
provider query
price-volume query
raw payload retention
extractor implementation
OOS execution
paper/live trading
strategy promotion
```

Next work requires separate explicit approval before any probe runner, output directory or ledger entry can be created.

See [[Report-XMOM-Earnings-Single-Probe-Approval-2026-05-21]].
