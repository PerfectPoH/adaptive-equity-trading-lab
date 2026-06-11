---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-KRONOS-DEFENSE-001
ultimo-aggiornamento: 2026-06-11
tags: [kronos, defense, risk-overlay, regime, oos]
---

# Report - Kronos Defense Duel (TRIAL-KRONOS-DEFENSE-001)

Decision: `KRONOS_DEFENSE_FAIL__G3_G4`

## Domanda

A parita' di esposizione media, l'overlay difensivo Kronos (forecast SPY)
riduce il drawdown del path OOS congelato (TRIAL-STUDIO-OOS-005) piu' del
baseline semplice (index regime classifier)?

## Protocollo

- Inference bounded autorizzata dall'owner: Kronos-mini CPU su snapshot SPY
  locale, 68 as-of dates (ogni 5 giorni di borsa, 2025-01 -> 2026-05),
  context 250 bar, pred_len 5, 20 sample path. Nessun download di mercato.
- Regole esposizione preregistrate, zero sweep (vedi modulo
  `kronos_defense_trial.py`).
- Confronto a parita' di esposizione media (0.789 entrambi).
- Baseline timing: 500 shift circolari dell'esposizione Kronos.

## Risultati

| Overlay | Return OOS | Max DD | Efficienza (DD salvato / return ceduto) |
|---|---|---|---|
| Nessuno | +49.6% | -7.5% | - |
| Kronos | +32.7% | -5.3% | 0.13 |
| **Regime classifier** | **+36.4%** | **-2.7%** | **0.36** |

Gates: G1 coverage 99.7% PASS; G2 riduce il DD PASS; **G3 FAIL** (il DD
Kronos batte solo il 19.4% degli shift casuali della sua stessa esposizione:
il merito non e' nel timing); **G4 FAIL** (il classifier semplice e' ~3x
piu' efficiente a parita' di esposizione).

## Verdetto

Kronos NON entra come overlay difensivo: perde il duello contro il
baseline gia' validato (index regime classifier, vol-ordering OOS
preservato). Coerente con l'evidenza archiviata CANDIDATE-006 (filtro alpha
al 62o percentile vs random; throttle non decisivo). Lo slot RISK_OVERLAY
resta al regime classifier. Eventuale ritorno su Kronos solo con un modello
piu' grande o feature diverse, sempre tramite questo stesso protocollo.

## Artifact

`experiments/runs/kronos_defense_001_20260611_114802/`


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
