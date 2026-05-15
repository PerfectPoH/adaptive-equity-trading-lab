---
tipo: devlog
data: 2026-05-15
agente: cascade
topic: small-cap-lessons-learned-data-quality
tags: [devlog, small-cap, data-quality, lessons-learned, governance]
---

# 2026-05-15 - Small-cap data-quality lessons learned

## Scope

Created a Lessons Learned report after the `yfinance` small-cap data-quality audit failure.

```text
No new trial opened.
No strategy backtest.
No validation.
No OOS.
No sweep.
```

## Decision

The 2026-05-09..2026-05-14 small-cap work is retroactively classified as methodological/infrastructure stress testing, not evidence of investible edge.

This includes smoke runs, setup disentangling, breakout ablations, temporal split validation, EMA200 diagnostics, OOS 2025 and `TRIAL-RANKEX-001`.

## Smoke sample check

A bounded ex-post check was added for the effective smoke 2 tickers:

```text
BBAI
LUNR
OPEN
OUST
```

Conservative result:

- `LUNR`: 2024 warrant exercise / new warrants / dilution event found.
- `BBAI`: 2024 warrant exercise agreements / dilution events found via issuer-hosted filing.
- `OPEN`: no counted 2024 material event in bounded light check.
- `OUST`: 2023 reverse split plus 2024 listing/warrant venue transfer.

## Governance consequence

The smoke 2 verdict `beats_primary_benchmark` is reclassified as:

```text
pipeline smoke success
not strategy evidence
not edge evidence
not promotion evidence
```

The next allowed path remains a fixed-universe large-cap/ETF negative control, but only after scaffolding rules and property-based pass/fail criteria are predeclared.

Vedi [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]], [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
