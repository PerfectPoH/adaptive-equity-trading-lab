---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-STUDIO-OOS-008
ultimo-aggiornamento: 2026-06-11
tags: [audit-response, baseline, permutation, routing, oos]
---

# Report - Honest Baselines Trial (TRIAL-STUDIO-OOS-008)

Decision: `ROUTING_SKILL_NOT_CONFIRMED__S3`

## Contesto

Risposta operativa a [[Report-External-Audit-2026-06-11]] (B1 cost-tier
artifact, B2 duplicati). Audit VERIFICATO: numeri riprodotti esattamente.
Pool dedup (92 componenti, 12 duplicati rimossi), vol-norm in-sample,
ricetta congelata, cutoff 2025-01-01, OOS 2025-01 -> 2026-05.

## La decomposizione onesta del delta headline (+72.5pp)

| Baseline | OOS total | Delta vs dynamic (+49.6%) |
|---|---|---|
| static_all (legacy, USATA nei trial 005-007) | -22.8% | +72.5pp |
| **static cost-matched (<=100bps, onesta)** | **+29.2%** | **+20.5pp** |
| unconditional top-5 IS Sharpe (no routing) | +8.4% | +41.3pp |

L'audit aveva stimato ~+20pp di delta onesto: confermato al decimale.
~52pp del delta headline erano l'artefatto dei cost tier.

## Permutation test (il test che mancava)

200 shift circolari delle label di regime, stessi basket congelati:
- permuted mean: +26.2%, p95: +54.3%
- reale: +49.6% -> **p = 0.115**

Gates: S1 batte la static onesta PASS; S2 batte la selezione unconditional
PASS; S3 significativita' del TIMING di regime **FAIL** (p > 0.05).

## Verdetto

La SELEZIONE per regime sopravvive alle baseline oneste (+20pp). Il TIMING
di regime - usare il basket giusto nel momento giusto - e' suggestivo ma
NON statisticamente dimostrato su questo campione: gran parte del valore
viene dal tenere componenti buoni, non dallo switching. Il claim
"BEATS_STATIC" dei trial 005-007 va letto con questa decomposizione.

## Azioni gia' prese

1. Dedup per hash dello stream nel trial (B2).
2. Baseline cost-matched e unconditional nel protocollo.
3. Permutation test cablato e riusabile.

Vedi backlog per i fix rimanenti dell'audit (B5 entry_bar_exit_touch,
trial counter automatico, sizing MVP, benchmark total-return).

## Artifact

`experiments/runs/honest_baselines_008_20260611_155947/`

---

## Addendum (follow-up audit, stesso giorno)

Correzioni applicate: p-value con convenzione `(1+c)/(n+1)` (p=0.1194, verdetto
invariato); f-string portabile in databento_probe; companion gate aggiunto
alla replica mensile schedulata (il protocollo congelato resta intatto, ma
ogni replica esegue anche queste baseline).

### Membership vs timing: la decomposizione finale

Nuova metrica `membership_blend_static`: i basket per-regime tenuti STATICI
(media dei pesi, mai switching).

| Ipotesi | OOS | Incremento |
|---|---|---|
| Unconditional top-5 (niente router) | +8.4% | - |
| **+ MEMBERSHIP del router (blend statico)** | **+41.1%** | **+32.7pp** |
| + TIMING (switching per regime) | +49.6% | +8.5pp (p=0.119, n.s.) |

L'asset reale del router e' la MEMBERSHIP: quali componenti ammette per
regime vale +32.7pp sulla selezione semplice e si trasferisce OOS senza
bisogno di switching. Il timing aggiunge +8.5pp non distinguibili dal caso.
La replica mensile trattera' le due ipotesi separatamente (prompt aggiornato).
