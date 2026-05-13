---
tipo: devlog
data: 2026-05-13
agente: cascade
topic: small-cap-setup-archive-decision
tags: [devlog, small-cap, decision, archive, validation, ranking-exits]
---

# 2026-05-13 - Small-Cap Setup Archive Decision

## Decisione

Il setup portfolio corrente viene archiviato come strategia non promuovibile.

Setup archiviato:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filter = iwm_close > iwm_ema_200
holding_period_bars = 5
risk_fraction = 0.01
```

Verdetto operativo:

```text
Tooling promosso.
Risk-based sizing promosso.
Setup non promosso come portfolio strategy.
No paper trading.
No ranking production.
No nuovi filtri in-sample per salvare questa ipotesi.
```

## Evidenza conclusiva

### OOS 2025 con sizing corretto

```text
portfolio return = +0.92%
ticker_holding_window = +3.05%
random_entry_baseline = +3.92%
pnl_excluding_top_3 = -6,973.98
sign_flip_excluding_top_3 = true
```

### Multi-year 2022-2024 EMA200 con sizing corretto

```text
portfolio return = +3.60%
ticker_holding_window = +5.42%
random_entry_baseline = +4.16%
equal_weight_universe = +11.93%
pnl_excluding_top_3 = -5,339.52
sign_flip_excluding_top_3 = true
```

### Interpretazione

Il fix risk-based sizing ha rimosso il bug infrastrutturale:

```text
insufficient_funds OOS: 18 -> 0
insufficient_funds multi-year EMA200: 8 -> 0
```

Ma quando il motore smette di allocare quasi all-in, il vecchio edge portfolio non sopravvive:

```text
old multi-year EMA200 return: +169.21%
corrected risk-sizing return: +3.60%
```

Quindi il vecchio risultato era largamente leverage/path artifact.

## Decisione metodologica

Questo non invalida il laboratorio o il tooling. Invalida solo questa specifica ipotesi come strategia portfolio pronta.

Lo stato corretto e':

```text
infrastructure validata
research hypothesis archiviata
```

## Track separato consentito

E' consentito aprire in futuro un track separato su:

```text
ranking intra-candidate
exit management
portfolio construction
correlation / clustering exposure
```

Vincoli obbligatori:

1. nuovo trial accounting esplicito;
2. nessuna retro-promozione dei risultati 2022-2025;
3. nessun riuso del vecchio +169% come prova di edge;
4. confronto contro ticker holding window, random entry, equal-weight universe ed ex-topN;
5. OOS/universe robustness prima di qualunque paper trading.

## Stato finale della track corrente

```text
ARCHIVED / NOT PROMOTED
```

Vedi [[2026-05-12-cascade-small-cap-multiyear-risk-sizing-rerun]], [[2026-05-12-cascade-small-cap-risk-based-sizing-fix]], [[Report-Small-Cap-Research-Status-2026-05-12]], [[Roadmap-Master]], [[backlog]].
