---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-data-quality-gate-decision
tags: [devlog, small-cap, data-quality, methodology, governance]
---

# 2026-05-14 - Small-cap data quality gate decision

## Contesto

Dopo la chiusura di `TRIAL-RANKEX-001` e del ranking semplice, il feedback metodologico evidenzia che il prossimo collo di bottiglia non e' solo il segnale, ma la qualita' del righello:

```text
data quality
survivorship / universe as-of
random baseline distribution
multiple testing ledger
backtester audit
news/event blindness
category-level stop rule
```

## Decisione

```text
NO TRIAL-XMOM-001 YET
DATA QUALITY AND METHODOLOGY GATE FIRST
```

## Prossimo lavoro ammesso

Solo lavoro documentale/metodologico:

```text
1. data-quality audit spec for yfinance small-cap
2. bootstrap random baseline requirement
3. multiple-testing ledger requirement
4. SmallCapPortfolioBacktester audit plan
5. category-level trial budget / stop rule
```

## Stato operativo

```text
No backtest.
No validation.
No OOS.
No sweep.
No paper trading.
```

Vedi [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
