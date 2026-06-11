---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-TRUE-ETF-001
ultimo-aggiornamento: 2026-06-11
tags: [true-backtest, etf, capital-aware, oos, dsr, reality-check]
---

# Report - True ETF Backtest (TRIAL-TRUE-ETF-001)

Decision: `TRUE_ETF_FAIL__G3_G4` (3 gate su 5 passate)

## Primo backtest del progetto su dati reali con capitale reale

Spec congelata + Emendamento 001 ([[TRIAL-TRUE-ETF-001-Spec]]): regole CAUSALI
(soglie rolling 252d), entry next-open, cash accounting (no leva, max 10
posizioni, 10% equity/posizione), costi 100 bps round-trip, dati yfinance
auto-adjusted scaricati su autorizzazione owner (20 simboli, 2018 -> 2026-06-10).
OOS: 2024-01 -> 2026-06.

## Risultati OOS

| Metrica | Difeso (classifier) | Non difeso | SPY buy-hold |
|---|---|---|---|
| Return | +54.0% | +113.9% | +57.7% |
| Max DD | -13.7% | -19.8% | -18.8% |
| Return/DD | 3.95 | 5.76 | 3.08 |

| Gate | Esito |
|---|---|
| G1 batte SPY risk-adjusted | PASS |
| G2 no sign flip ex-top3 | PASS (+121k ex-top3) |
| G3 DSR | **FAIL** (Sharpe daily 0.080, DSR 0.03) |
| G4 N >= 100 trade | **FAIL** (40 trade) |
| G5 sopravvive a costi doppi | PASS |

## Lettura onesta (tre lezioni dal mondo reale)

1. **La struttura regge anche su dati veri**: batte SPY risk-adjusted, e' robusta
   ex-top3 e ai costi. Non e' rumore puro.
2. **Il gap proxy->reale e' grande**: Sharpe daily da 0.35 (stream proxy) a
   0.080 (capitale reale). I numeri proxy SOVRASTIMANO, come il lab ha sempre
   sospettato.
3. **La difesa del classifier su dati reali FA PEGGIO** risk-adjusted (3.95 vs
   5.76 non difeso): il risultato HOUSE su proxy non si trasferisce. Lezione
   chiave per il router.

Nota di fragilita': con costi doppi il return e' piu' ALTO (+69.8%) del base -
con 40 trade il path domina (i costi cambiano quali trade entrano). Conferma
G4: il campione e' troppo piccolo per qualsiasi claim.

## Prossimo passo ammesso

TRIAL-TRUE-ETF-002 (da preregistrare): holding 90d (variante gia' nel set
congelato dei vincitori) per aumentare N verso >=100, DSR a trial_count=3
(seconda configurazione guardata). Nessun altro parametro toccato.

## Artifact

`experiments/runs/true_etf_001_20260611_122029/` (equity, trade log, gates).
