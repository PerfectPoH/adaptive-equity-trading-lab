---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-pivot
tags: [devlog, pivot, small-cap, swing, long-only]
---

# 2026-05-09 - Small-Cap Swing Pivot

## Contesto

Dopo backtest analysis, la baseline large-cap ML resta metodologicamente valida ma non mostra edge sufficiente contro buy-and-hold. Continuare a ottimizzare soglie e filtri sulla stessa baseline rischia di diventare data-mining.

## Decisione

Congelare la baseline large-cap ML come controllo negativo e aprire una research track separata: **long-only small/mid-cap swing**.

Short selling escluso dalla fase iniziale per evitare hard-to-borrow, borrow fees e disponibilita' borrow non modellabile nei dati storici retail.

## Cosa e' stato aggiunto

- Nuova spec: [[small-cap-swing-research-spec]].
- Roadmap aggiornata con Milestone 3B.
- Backlog rischi aggiornato con:
  - RISK-015: spread/slippage/fill su small-cap;
  - RISK-016: dilution/offering risk;
  - RISK-017: capacity constraint.

## Prossima mossa

Prima implementazione consigliata: universe builder small/mid-cap con filtri liquidita', prezzo e dollar volume, seguito da data-quality report. Nessun ML finche' scanner, dati, costi e benchmark non sono definiti.

Vedi [[Roadmap-Master]], [[Quant-Research-Priorities-2026-05-09]], [[2026-05-09-cascade-backtest-analysis]].
