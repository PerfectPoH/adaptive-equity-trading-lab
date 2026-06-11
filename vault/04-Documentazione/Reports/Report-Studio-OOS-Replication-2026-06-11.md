---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-STUDIO-OOS-002
ultimo-aggiornamento: 2026-06-11
tags: [oos, regime, portfolio, dsr, replication, outlier]
---

# Report - Studio OOS Replication (TRIAL-STUDIO-OOS-002)

Decision: `OOS_POSITIVE__BEATS_STATIC__OUTLIER_FRAGILE__DSR_FAIL`

## Protocollo

Replica di [[Report-Studio-OOS-Validation-2026-06-11]] con cutoff anticipato:
selezione congelata su dati fino al `2024-01-01`, replay OOS 2024-01 -> 2026-05.
Artifact: `experiments/runs/studio_oos_002_20260611_111443/`.

## Risultati vs trial 001

| Gate | OOS-001 (cutoff 2025) | OOS-002 (cutoff 2024) |
|---|---|---|
| OOS positivo | PASS +61.50 u | PASS +88.96 u |
| Batte static | PASS delta +57.76 u | PASS delta +83.49 u |
| Ex-top3 robusto | PASS +7.46 u | **FAIL -0.51 u, SIGN FLIP** |
| DSR | FAIL (0.0) | FAIL (0.0) |

## Fatto chiave

I top-3 contributor coincidono quasi del tutto nei due trial
(`a42078cbf0a2ea94`, `9474fe601e0f2bd2` presenti in entrambi): l'intero
vantaggio dynamic-vs-static e' concentrato negli stessi 2-3 stream proxy.
Sono anche gli stream a maggiore ampiezza (|r| max ~18), quindi in
aggregazione additiva dominano il contributo per costruzione di scala,
non necessariamente per qualita'.

## Verdetto per la regola del lab

Per la regola "se il risultato cambia segno senza i top 3 winner, niente
promozione": la replica fallisce. La capacita' di selezione dell'engine
NON e' validata. OOS-001 era il caso fortunato, OOS-002 mostra la
fragilita' strutturale.

## Lezione ingegneristica

In aggregazione additiva gli stream ad ampiezza alta dominano qualunque
basket. Prima di nuovi trial: normalizzare gli stream a volatilita'
unitaria (o rank-based) nel composer, poi ripetere il protocollo a due
cutoff. Senza questa correzione ogni "best basket" e' in larga parte un
artefatto di scala.

## Governance

Nessuna promozione. Nessuna provider query. Stream proxy.
