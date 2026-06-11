---
tipo: stato-corrente
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-06-11
tags: [stato, snapshot, operativo]
---

# Stato Corrente

> Nota viva: sovrascrivere a ogni sessione. La storia sta nei devlog e nei report.

## Policy attiva

- Modalita': `RISK_REGIME_ENGINE_ONLY` - 0 strategie promosse, no paper/live.
- Protocollo OOS Studio: **CONGELATO** dal 2026-06-11. Replica mensile schedulata
  (primo del mese): nessuna modifica ammessa a regola/parametri.

## Risultato di riferimento (2026-06-11)

- [[Report-Studio-OOS-Preregistered-Rule-2026-06-11]]: regola preregistrata
  top-5 Sharpe per regime, vol-norm - tutte le gate passate su 3 cutoff.
- [[Report-House-Portfolio-Trial-2026-06-11]]: ricetta + difesa classifier =
  +35.8%/-2.8% DD (2025) e +66.8%/-4.3% DD (2024), tutte le gate passate.
- [[Report-Kronos-Defense-Duel-2026-06-11]]: Kronos NON entra come difesa
  (perde 3x dal classifier). Slot RISK_OVERLAY al regime classifier.

## Strumenti attivi

- Sito: `dashboard/studio.py` su porta 8502 (Portfolio Studio); `app.py` legacy audit.
- Difesa validata: `src/risk/index_regime_classifier.py` (2 validazioni OOS).
- Gate statistiche: DSR + multiplicity budget cablati nel runner OOS.

## Prossimo passo canonico

1. FAMIGLIA TRUE-ETF CHIUSA ([[Report-True-ETF-Family-Closure-2026-06-11]]):
   3 configurazioni, nessuna passa. Restano DUE strade, decisione owner:
   (a) data bundle a pagamento (Norgate/Sharadar) per small-cap/eventi con
   PIT veri; (b) fermare il programma alpha e tenere lab + replica mensile.
2. Routing per regime: claim ridimensionato da audit + permutation test
   ([[Report-Honest-Baselines-Trial-2026-06-11]]): MEMBERSHIP +32.7pp
   (ipotesi principale), TIMING +8.5pp non significativo (p=0.119).
   Criterio di successo PREREGISTRATO per la membership:
   [[Criterio-Preregistrato-Membership-2026-06]] (6 mesi, 5/6 positivi,
   delta cumulato >0, DSR a multiplicita' di famiglia). PREREQUISITO
   BLOCCANTE: RISK-044 (refresh dati) entro il 2026-07-01, altrimenti il
   conteggio non parte.
3. Igiene in corso: RISK-041 (fix look-ahead MVP) in lavorazione,
   RISK-042 (trial counter) CHIUSO e cablato.

## Da NON fare

- Toccare la regola congelata prima della replica.
- Promuovere qualsiasi cosa su stream proxy.
- Nuovi trial senza preregistrazione con DSR/multiplicity budget.
