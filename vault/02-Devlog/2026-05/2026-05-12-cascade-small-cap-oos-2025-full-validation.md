---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-oos-2025-full-validation
tags: [devlog, small-cap, oos, validation, full-year-2025, failed-gate, breakout-continuation]
---

# 2026-05-12 - Small-Cap OOS Full-Year 2025 Validation

## Obiettivo

Estendere il test OOS H1 2025 all'intero 2025 per verificare se il fallimento H1 fosse solo sample-size noise o un vero problema di validazione.

Regole congelate:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
holding_period_bars = 5
no ranking
no new filters
```

## Run

```text
experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_full_20260512
```

Periodo risolto dal manifest:

```text
2025-01-02 -> 2025-12-29
```

## Confronto H1 vs full-year

| Run | Trades | P&L | Return | Rejections | Ticker HW | Random entry | IWM | Equal-weight |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OOS H1 2025 | 2 | -16,093.19 | -16.09% | 82 | -6.77% | 5.43% | -1.42% | 1.16% |
| OOS full 2025 | 15 | -15,906.64 | -15.91% | 242 | 3.05% | 3.92% | -1.18% | -2.22% |

## Risultato full-year

| Metric | Value |
|---|---:|
| Trades | 15 |
| Total P&L | -15,906.64 |
| Return | -15.91% |
| Win rate | 33.33% |
| P&L ex top1 | -57,079.07 |
| P&L ex top3 | -89,989.79 |
| Total rejections | 242 |

Nota: il P&L ex-top1/ex-top3 peggiora perche' la run e' gia' negativa e rimuovere i vincitori rende evidente la fragilita' della distribuzione.

## Rejections

| Reason | Count |
|---|---:|
| setup_excluded | 156 |
| feature_filtered | 61 |
| insufficient_funds | 18 |
| regime_filtered | 7 |

## Trade list full-year

| Symbol | Signal date | P&L | Return | Score | O2C | RelVol20d | VIX |
|---|---|---:|---:|---:|---:|---:|---:|
| CERS | 2025-01-27 | -4,029.84 | -13.54% | 83.33 | 12.57% | 2.35 | 17.90 |
| PRCH | 2025-06-06 | 1,209.32 | 1.26% | 83.33 | 13.13% | 1.57 | 16.77 |
| MVST | 2025-06-16 | -16,653.87 | -17.14% | 100.00 | 14.89% | 1.61 | 19.11 |
| AMPX | 2025-06-26 | 10,434.65 | 12.96% | 83.33 | 12.96% | 2.09 | 16.59 |
| SANA | 2025-07-08 | 2,331.17 | 2.56% | 83.33 | 22.33% | 2.42 | 16.81 |
| IOVA | 2025-07-16 | 41,172.44 | 44.13% | 83.33 | 15.54% | 1.92 | 17.16 |
| CABA | 2025-08-13 | -1,046.73 | -5.14% | 83.33 | 24.82% | 4.30 | 14.49 |
| OUST | 2025-08-13 | -7,478.54 | -6.56% | 83.33 | 11.20% | 1.60 | 14.49 |
| EOSE | 2025-09-02 | -14,252.51 | -11.32% | 83.33 | 11.92% | 1.70 | 17.17 |
| EOSE | 2025-09-12 | 22,476.07 | 20.13% | 100.00 | 13.26% | 1.62 | 14.76 |
| OUST | 2025-10-14 | -31,498.62 | -23.48% | 83.33 | 20.98% | 1.55 | 20.81 |
| KURA | 2025-10-27 | -11,042.20 | -10.76% | 100.00 | 12.65% | 2.35 | 15.79 |
| CERS | 2025-11-07 | -2,119.42 | -11.41% | 83.33 | 19.58% | 2.78 | 19.08 |
| CERS | 2025-12-11 | -1,107.17 | -4.20% | 83.33 | 11.40% | 1.53 | 14.85 |
| SHLS | 2025-12-11 | -4,301.39 | -6.81% | 83.33 | 13.49% | 1.60 | 14.85 |

## Monthly breakdown

| Month | Trades | P&L | Win rate | Median return |
|---|---:|---:|---:|---:|
| 2025-01 | 1 | -4,029.84 | 0.00% | -13.54% |
| 2025-06 | 3 | -5,009.90 | 66.67% | 1.26% |
| 2025-07 | 2 | 43,503.60 | 100.00% | 23.35% |
| 2025-08 | 2 | -8,525.27 | 0.00% | -5.85% |
| 2025-09 | 2 | 8,223.56 | 50.00% | 4.40% |
| 2025-10 | 2 | -42,540.81 | 0.00% | -17.12% |
| 2025-11 | 1 | -2,119.42 | 0.00% | -11.41% |
| 2025-12 | 2 | -5,408.56 | 0.00% | -5.51% |

## Interpretazione

### 1. H1 non era solo sample-size noise

Full-year porta i trade da 2 a 15 ma il risultato resta quasi identico:

```text
H1: -16.09%
Full-year: -15.91%
```

Questo conferma che il gate OOS non e' superato.

### 2. Il portfolio perde mentre il filtered benchmark e' positivo

Nel full-year 2025:

```text
ticker_holding_window: +3.05%
random_entry_baseline: +3.92%
portfolio: -15.91%
```

Questo indica che il problema non e' solo la presenza dei segnali, ma la combinazione di path, sizing, capitale disponibile e selezione tra candidati concorrenti.

### 3. Ranking grezzo non e' risolutivo

Due trade con score 100 sono perdenti importanti:

```text
MVST 2025-06-16: -17.14%
KURA 2025-10-27: -10.76%
```

Quindi non basta promuovere lo scanner score attuale a ranking decisionale.

### 4. Distribuzione fragile

La run vive di luglio positivo e viene annullata da ottobre:

```text
July: +43.5k
October: -42.5k
```

Non c'e' robustezza temporale sufficiente.

## Verdict

```text
OOS full-year 2025 conferma che la strategia NON e' validata.
```

Blocco esplicito:

```text
no paper trading
no ranking production
no nuovi filtri in-sample per riparare il 2025
```

## Prossimo passo consigliato

Non ottimizzare sul 2025. La prossima mossa metodologica e':

1. **Trial accounting / DSR prep**: contare setup, soglie, regime gate e finestre provate.
2. **Universe robustness**: usare un universo alternativo prima di nuove feature.
3. **Portfolio mechanics audit**: capire perche' il portfolio perde mentre il filtered ticker benchmark e' positivo.

Vedi [[2026-05-12-cascade-small-cap-oos-2025-h1-validation]], [[2026-05-12-cascade-small-cap-ema200-regime-gate-ablation]], [[Roadmap-Master]], [[backlog]].
