---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-rankex-strategic-decision
tags: [devlog, small-cap, rankex, decision, governance]
---

# 2026-05-14 - RankEx strategic decision

## Contesto

Dopo la validation failure di `TRIAL-RANKEX-001`, sono stati valutati i commenti dei colleghi e il bivio tra:

```text
A. chiudere il ranking semplice
B. aprire subito un nuovo trial feature-ranking
```

## Decisione

```text
CLOSE SIMPLE RANKING TRACK
DO NOT OPEN TRIAL-RANKEX-002 YET
```

## Razionale

`TRIAL-RANKEX-001` ha validato il laboratorio, non il segnale:

```text
portfolio_return: 5.62%
pnl_excluding_top_3: -6282.54
sign_flip_excluding_top_3: true
insufficient_funds: 0
```

Quindi:

```text
infrastruttura OK
ranking semplice non robusto
trial chiuso
```

## Prossima direzione preferita

```text
Cross-Sectional Momentum vs IWM
```

Da trattare solo come nuova ipotesi con nuovo trial ID, nuova pre-registrazione e nessuna run preventiva.

## Stato operativo

```text
NO OOS 2025 for TRIAL-RANKEX-001
NO PAPER TRADING
NO DISCRETIONARY SWEEP
NEXT: draft preregistered cross-sectional momentum spec only
```

Vedi [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]], [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]].
