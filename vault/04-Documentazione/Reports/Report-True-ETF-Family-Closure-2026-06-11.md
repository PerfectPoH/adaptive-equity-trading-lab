---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-TRUE-ETF-003
ultimo-aggiornamento: 2026-06-11
tags: [true-backtest, etf, family-closure, oos, trial-counter]
---

# Report - Chiusura famiglia TRUE-ETF (TRIAL-TRUE-ETF-003)

Decision: `TRUE_ETF_FAIL__G1_G3_G4` -> **FAMIGLIA CHIUSA SU DATI GRATUITI**

## Ultimo tentativo dichiarato (Emendamento 002)

Universo ampliato a 55 ETF correnti, regole/holding/costi identici al 001.
DSR dichiarata a trial_count=4 + riporto automatico dal trial counter
(RISK-042, primo utilizzo).

## Risultati OOS (2024-01 -> 2026-06)

| Metrica | 003 (55 ETF) | 001 (12 ETF + large cap) | SPY |
|---|---|---|---|
| Return | +33.8% | +54.0% | +57.7% |
| Return/DD | 2.28 | 3.95 | 3.08 |
| Trade | 41 | 40 | - |
| Non difeso | +58.9% / -16.2% | +113.9% / -19.8% | +57.7% / -18.8% |

DSR: 0 alla multiplicita' dichiarata (4), di famiglia (3) e **di programma
(133 run reali contati)**. Il trade count NON cresce con l'universo: con 10
posizioni max e holding 180d il portafoglio e' sempre pieno - limite
strutturale, non di universo.

## Decisione di famiglia

```text
FAMIGLIA TRUE-ETF (momentum/meanrev/dollarbar causali, universi ETF gratuiti):
CHIUSA. 3 configurazioni, nessuna passa le gate. Il non difeso replica circa
buy-and-hold; la difesa toglie rendimento senza guadagno risk-adjusted
sufficiente; N non puo' salire senza cambiare struttura (= nuova famiglia).
```

## Stato del programma dopo oggi

- 11 trial eseguiti in un giorno, 4 famiglie falsificate onestamente
  (Kronos difensivo, difesa-su-reale, recipe ETF ristretta e ampia),
  1 protocollo congelato in replica mensile, 1 claim ridimensionato da audit.
- Trial counter di programma ora cablato nel runner: la multiplicita' onesta
  e' visibile in ogni verdetto futuro.

## Le due strade rimaste (decisione owner, nessuna terza)

1. **Data bundle a pagamento** (Norgate/Sharadar): testare le strategie dove
   sono nate (small-cap, eventi) con PIT/delisted veri.
2. **Fermarsi qui con il programma alpha** e tenere il lab come infrastruttura
   + replica mensile: risultato gia' di valore.

Vedi [[Report-External-Audit-2026-06-11]], [[Stato-Corrente]].
