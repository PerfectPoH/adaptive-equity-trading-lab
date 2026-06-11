---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-STUDIO-OOS-001
ultimo-aggiornamento: 2026-06-11
tags: [oos, regime, portfolio, dsr, validation]
---

# Report - Studio OOS Validation (TRIAL-STUDIO-OOS-001)

Decision: `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_FAIL`

## Domanda

La selezione per-regime del Regime Portfolio Studio generalizza su dati mai
visti, o memorizza il passato?

## Protocollo

- Stream componenti troncati al `2025-01-01` (1.682 periodi in-sample).
- `run_regime_studio` sceglie i basket per regime SOLO sul pre-cutoff.
- Ricetta congelata, replay su 333 periodi OOS (2025-01 -> 2026-05).
- Runner: `python -m src.experiments.studio_oos_runner`.
- Artifact: `experiments/runs/studio_oos_001_20260611_110922/`.

## Risultati (unita' additive proxy, non percentuali)

| Gate | Esito |
|---|---|
| OOS positivo | PASS - dynamic `+61.50 u` |
| Batte la baseline statica | PASS - static `+3.74 u`, delta `+57.76 u` |
| Robustezza ex-top3 | PASS - `+7.46 u` senza i 3 migliori, nessun sign flip |
| DSR (deflazionato per 60 trial cercati) | **FAIL** - Sharpe daily 0.286 vs benchmark multiplicita' 0.689, DSR 0.0 |

Capital sim illustrativa (exposure 10%, clip +/-0.5, 55 periodi clippati):
+868.9% / DD -59.4%. NON interpretabile come P&L: gli stream restano somme
additive di trade proxy, la sim serve solo a vedere la forma del path.

## Lettura onesta

1. Prima volta che la gate DSR dormiente viene collegata a un trial reale.
2. L'engine NON memorizza soltanto: la struttura per-regime trasferisce
   sul periodo mai visto (+61.5 vs +3.7 static) e sopravvive all'ex-top3,
   che storicamente ha ucciso quasi tutto in questo lab.
3. Ma per lo standard del lab il segnale non e' distinguibile dal "migliore
   di 60 tentativi su rumore": DSR 0. La deflazione e' volutamente severa
   (applica l'intera multiplicita' della ricerca al risultato OOS singolo).
4. Limiti permanenti: stream proxy additivi, componenti sopravvissuti a
   selezione, niente dati PIT/delisted. Nessuna promozione.

## Prossimo passo ammesso

Allungare l'OOS o ridurre la multiplicita' (meno candidati, preregistrati)
per dare alla DSR una chance reale; oppure ripetere il protocollo su un
secondo cutoff (2024-01-01) come replica.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
