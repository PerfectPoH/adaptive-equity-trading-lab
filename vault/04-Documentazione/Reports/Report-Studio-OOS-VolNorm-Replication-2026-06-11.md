---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-STUDIO-OOS-003, TRIAL-STUDIO-OOS-004
ultimo-aggiornamento: 2026-06-11
tags: [oos, regime, portfolio, dsr, vol-normalization, replication]
---

# Report - Studio OOS con Vol Normalization (TRIAL 003 + 004)

Decision: `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_FAIL` su ENTRAMBI i cutoff.

## Cosa e' cambiato rispetto a 001/002

Stream normalizzati a volatilita' unitaria (target 1%/periodo) con fattori
calcolati SOLO sull'in-sample (niente leak). Effetti: (a) gli stream ad
ampiezza alta non dominano piu' per costruzione di scala; (b) gli stream
normalizzati sono rendimenti frazionari plausibili, quindi i risultati sono
PERCENTUALI compounded vere, non "unita'".

## Risultati replicati su due cutoff

| Metrica | 003 (cutoff 2025-01) | 004 (cutoff 2024-01) |
|---|---|---|
| Dynamic OOS | **+51.2%** | **+70.2%** |
| Static OOS | -22.9% | -38.0% |
| Delta | +74.1 pp | +108.2 pp |
| Max DD dynamic | -3.9% | -9.1% |
| Ex-top3 | +19.4%, no flip | +14.2%, no flip |
| Sharpe daily | 0.347 | 0.279 |
| DSR (60 trial, std 0.29-0.33) | FAIL (0.0) | FAIL (0.0) |

Artifact: `experiments/runs/studio_oos_003_20260611_112114/`,
`experiments/runs/studio_oos_004_*/`.

## Lettura

1. La fragilita' outlier del trial 002 era davvero un artefatto di scala:
   con stream equalizzati la robustezza ex-top3 REPLICA su entrambi i cutoff.
2. La struttura per-regime aggiunge valore consistente: la baseline statica
   equal-weight PERDE in OOS (-23%/-38%), il routing per regime guadagna.
3. Top contributor ricorrenti: Factory Dollar-Bar Microstructure 180d,
   Factory Mean Reversion 180d, Factory Momentum 90/180d - tutti template
   factory con 1.000+ trade, non micro-campioni.
4. DSR resta FAIL su entrambi: contro il benchmark deflazionato per 60
   candidati (Sharpe daily richiesto ~0.7-0.78) il segnale non basta.
   Nota tecnica: vs zero il Sharpe OOS e' fortemente significativo
   (t~6 su 333-590 periodi); e' il confronto col "best of 60" che non passa.
   La deflazione applicata e' conservativa: tratta il singolo path OOS come
   se fosse il migliore cercato, mentre la selezione e' avvenuta in-sample.

## Verdetto

La selezione per-regime dell'engine REGGE strutturalmente: replica su due
cutoff, sopravvive all'ex-top3, batte una baseline che perde. NON supera
la barra statistica deflazionata del lab, quindi: nessuna promozione,
nessun capitale. E' pero' il primo risultato del progetto che replica
attraverso protocollo, cutoff e stress outlier.

## Limiti permanenti

Stream proxy da dry-run, pool di strategie sopravvissute, niente dati
PIT/delisted, costi dichiarati ma non simulati a livello portfolio.
Il "true backtest" resta vincolato alla decisione dati (Norgate/Sharadar
o pivot ETF).

## Prossimo passo ammesso

1. Ridurre la multiplicita' della ricerca (candidati preregistrati <=10)
   per dare alla DSR una barra raggiungibile e onesta.
2. Replicare su un terzo cutoff (2023-01-01) come ulteriore conferma.
3. Solo dopo: discutere il data bundle per il true backtest.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
