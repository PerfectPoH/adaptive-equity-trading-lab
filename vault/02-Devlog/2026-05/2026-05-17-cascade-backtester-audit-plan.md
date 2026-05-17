# 2026-05-17 - Backtester audit plan

## Contesto

`RISK-043` richiedeva un audit documentale/TDD del `SmallCapPortfolioBacktester` dopo il bug `risk_fraction` (`BUG-037`).

## Cosa e' stato creato

Creato [[Report-Backtester-Audit-Plan-2026-05-17]].

La spec copre:

- risk-fraction sizing;
- cash ledger timing;
- entry/exit bar mechanics;
- cost model;
- concurrent candidates/ranking;
- filters/regime gates;
- rejection ledger integrity;
- equity curve reconciliation;
- limitations da documentare.

## Stato

```text
SPEC ONLY / NOT EXECUTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Decisione

Prima di qualunque nuovo trial small-cap, il progetto deve eseguire questo audit o dichiarare perche' il trial futuro non dipende dal `SmallCapPortfolioBacktester`.
