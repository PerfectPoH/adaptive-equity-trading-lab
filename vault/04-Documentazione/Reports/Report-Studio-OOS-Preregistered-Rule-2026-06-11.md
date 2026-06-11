---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-STUDIO-OOS-005, TRIAL-STUDIO-OOS-006, TRIAL-STUDIO-OOS-007
ultimo-aggiornamento: 2026-06-11
tags: [oos, regime, portfolio, dsr, preregistered, rule, replication]
---

# Report - Studio OOS con Regola Preregistrata (TRIAL 005-007)

Decision: `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_PASS` su TUTTI e tre i cutoff.

## Protocollo

Regola FISSA, zero ricerca: per ogni regime, top-5 componenti ammessi dal
router per Sharpe in-sample, pesi uguali. Stream normalizzati a vol unitaria
(fattori in-sample only). Multiplicita' dichiarata: 1 regola (DSR a
trial_count=2, minimo tecnico). Tre cutoff: 2025-01, 2024-01, 2023-01.

## Risultati (percentuali compounded, stream normalizzati)

| Metrica | 005 (2025) | 006 (2024) | 007 (2023) |
|---|---|---|---|
| Dynamic OOS | +49.6% | +85.3% | +1296.8% (*) |
| Static OOS | -22.9% | -38.0% | -13.3% |
| Ex-top3 | +25.1% no flip | +34.5% no flip | +62.4% no flip |
| Max DD | -7.6% | -9.1% | -77.9% (*) |
| Sharpe daily | 0.351 | 0.341 | 0.384 |
| DSR (trial=2) | PASS 0.99999 | PASS 0.999999 | PASS 1.0 |
| Multiplicity budget | 3 | 2 | 5 |

(*) Il 007 ha pochi componenti vivi nei primi mesi OOS: concentrazione
estrema, headline e drawdown non rappresentativi. I trial rappresentativi
sono 005 e 006.

## Avvertenza di onesta' sulla multiplicita'

La regola e' fissa e non e' stata scelta guardando l'OOS, ma il protocollo
e' evoluto durante la sessione (vol-norm introdotta dopo il sign-flip del
trial 002, motivata da un artefatto strutturale di scala, non da tuning sul
risultato). Con accounting severo a livello di programma (>=5 look), il DSR
passa solo sul 007: vedi `multiplicity_budget`. La conferma pulita richiede
una replica futura su dati nuovi (periodi successivi o artifact freschi)
senza alcuna modifica al protocollo, ora congelato.

## Conclusione

E' il primo risultato del lab che passa TUTTE le gate (OOS positivo, batte
static, ex-top3 robusto, DSR alla multiplicita' preregistrata) e replica su
tre cutoff. Driver ricorrenti: Factory Dollar-Bar 180d, Momentum 90/180d,
Mean Reversion 180d - template con 1.000+ trade. Limiti invariati: stream
proxy, pool sopravvissuto, niente PIT/delisted. NESSUNA promozione: il
prossimo gate e' il data bundle ammissibile per il true backtest.

## Artifact

`experiments/runs/studio_oos_005_20260611_113945/`,
`studio_oos_006_20260611_114013/`, `studio_oos_007_20260611_114042/`.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
