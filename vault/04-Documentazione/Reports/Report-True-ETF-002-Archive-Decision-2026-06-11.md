---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-TRUE-ETF-002
ultimo-aggiornamento: 2026-06-11
tags: [true-backtest, etf, archive, oos, dsr]
---

# Report - True ETF 002 e decisione di archivio

Decision: `TRUE_ETF_FAIL__G1_G3_G4` (2/5) -> **CANDIDATE ARCHIVED**

## Protocollo

Identico a [[Report-True-ETF-Backtest-2026-06-11]] con UN solo cambio
preregistrato: holding 90d (variante del set congelato) per aumentare N.
DSR a trial_count=3 (seconda configurazione guardata).

## Risultati OOS (2024-01 -> 2026-06)

| Metrica | 002 (90d) | 001 (180d) | SPY |
|---|---|---|---|
| Return | +41.2% | +54.0% | +57.7% |
| Max DD | -14.8% | -13.7% | -18.8% |
| Return/DD | 2.79 | 3.95 | 3.08 |
| Trade | 76 | 40 | - |
| DSR | FAIL (~0) | FAIL (0.03) | - |

Gates 002: G2 (ex-top3) e G5 (costi doppi) PASS; G1 (batte SPY), G3 (DSR),
G4 (N>=100) FAIL.

## Decisione

Accorciare l'holding aumenta i trade ma DISTRUGGE il vantaggio risk-adjusted:
il 90d perde anche contro buy-and-hold. Il 180d batte SPY risk-adjusted ma
con N=40 e DSR fallita non e' validabile. Per le regole del lab:

```text
CANDIDATE TRUE-ETF (famiglie momentum/meanrev/dollarbar causali su universo
ETF/large-cap gratuito) -> ARCHIVIATO: nessun edge validabile con questo
universo e queste regole. Nessuna promozione.
```

## Cosa resta in piedi (e vale)

1. La PIPELINE proxy -> true backtest e' costruita e provata: regole causali,
   capitale reale, 5 gate cablate, un giorno dalla spec all'esecuzione.
2. Tre falsificazioni oneste in un giorno: Kronos difensivo, difesa classifier
   su dati reali (peggiorativa), recipe ETF.
3. Le opzioni rimaste sono due, entrambe decisioni owner:
   a. TRIAL-TRUE-ETF-003 preregistrato con universo ETF liquido ampliato
      (~50 simboli correnti, survivorship-light), trial_count=4 - ultima
      cartuccia gratuita;
   b. data bundle a pagamento per testare le strategie dove sono nate
      (small-cap con delisted/PIT).

## Artifact

`experiments/runs/true_etf_002_20260611_122415/`
