---
tipo: devlog
data: 2026-05-13
agente: cascade
topic: small-cap-ranking-exits-track-opened
tags: [devlog, small-cap, ranking, exits, research-track, trial-accounting]
---

# 2026-05-13 - Small-Cap Ranking/Exits Track Opened

## Obiettivo

Aprire un track separato su ranking intra-candidate, uscite e portfolio construction senza promuovere il setup small-cap breakout EMA200 archiviato.

## Decisione

Creato documento vivo:

```text
vault/01-Feature/small-cap-ranking-exits-research-track.md
```

Stato:

```text
PROPOSED / NOT IMPLEMENTED / NOT PROMOTED
```

## Guardrail

Questo track non puo' usare come prova di edge:

```text
old multi-year EMA200 +169.21%
```

Motivo:

```text
il rerun con risk-based sizing corretto ha prodotto solo +3.60%, sotto benchmark e con sign flip ex-top3
```

Blocco operativo mantenuto:

```text
no paper trading
no ranking production
no nuovi filtri in-sample per salvare il setup archiviato
```

## Research questions aperte

1. Ranking intra-candidate.
2. Exit management.
3. Portfolio construction.
4. Correlation / clustering exposure.

## Trial accounting iniziale

Ledger iniziale:

| Trial | Stato | Note |
|---|---|---|
| TRIAL-INFRA-001 | chiuso/promosso | risk-based sizing fix, trial infrastrutturale |
| TRIAL-ARCHIVE-001 | chiuso/non promosso | corrected breakout EMA200 validation |
| TRIAL-RANKEX-001 | aperto/design-only | nuovo track ranking/exits, nessun backtest |

## Prossimo passo consentito

Prima di qualunque esperimento:

```text
TDD del formato trial accounting nei manifest oppure definizione manuale del ledger
```

Non eseguire sweep o backtest ranking/exits finche' il trial ledger non e' definito.

Vedi [[small-cap-ranking-exits-research-track]], [[2026-05-13-cascade-small-cap-setup-archive-decision]], [[Roadmap-Master]], [[backlog]].
