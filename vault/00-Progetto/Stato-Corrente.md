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

1. [[TRIAL-TRUE-ETF-001-Spec]] - true backtest capital-aware su universo
   ETF/large-cap ammissibile con dati gratuiti (spec congelata, da implementare).
2. Replica mensile automatica del protocollo congelato (gia' schedulata).
3. Decisione owner sul data bundle (Norgate/Sharadar) solo se serve small-cap.

## Da NON fare

- Toccare la regola congelata prima della replica.
- Promuovere qualsiasi cosa su stream proxy.
- Nuovi trial senza preregistrazione con DSR/multiplicity budget.
