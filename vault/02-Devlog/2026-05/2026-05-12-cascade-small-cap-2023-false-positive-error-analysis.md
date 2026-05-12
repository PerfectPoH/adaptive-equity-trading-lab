---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-2023-false-positive-error-analysis
tags: [devlog, small-cap, error-analysis, false-positive, whipsaw, ema200, breakout-continuation]
---

# 2026-05-12 - Small-Cap 2023 False Positive Error Analysis

## Decisione

Dopo l'ablation attiva `iwm_close > iwm_ema_200`, la tentazione naturale era aggiungere subito un'altra feature o passare a ranking. Ho scelto invece una diagnostica passiva sui falsi positivi 2023.

Motivo:

```text
Prima di spendere nuovi gradi di liberta', bisogna capire perche' il gate EMA200 migliora il sistema ma non elimina il 2023 negativo.
```

Questa analisi non introduce nuovi filtri, non cambia lo scanner e non cambia il backtester.

## Run analizzata

```text
experiments/runs/small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_20260511
```

Config congelata:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
```

Artifact generati per diagnostica locale:

```text
portfolio_2023_false_positive_feature_diagnostics.csv
portfolio_2023_trade_error_analysis.csv
portfolio_2023_iwm_whipsaw_diagnostics.csv
```

## 2023 trade list

### Perdenti 2023

| Symbol | Signal date | P&L | Return | O2C | RelVol20d | Intraday range | ATR pct | IWM dist EMA200 | VIX |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ARRY | 2023-12-13 | -12,028.40 | -11.62% | 11.41% | 1.63 | 11.27% | 4.79% | 7.02% | 12.19 |
| OUST | 2023-12-26 | -11,446.10 | -18.15% | 12.33% | 1.75 | 12.56% | 6.42% | 12.08% | 12.99 |
| PRCH | 2023-01-17 | -4,972.81 | -14.09% | 11.67% | 1.70 | 15.86% | 8.13% | 1.22% | 19.36 |
| NVTS | 2023-02-01 | -2,207.47 | -4.72% | 10.76% | 1.85 | 11.33% | 5.51% | 5.19% | 17.87 |
| MVST | 2023-07-11 | -231.30 | -0.62% | 10.13% | 2.42 | 13.60% | 6.83% | 4.23% | 14.84 |

### Vincitori 2023

| Symbol | Signal date | P&L | Return | O2C | RelVol20d | Intraday range | ATR pct | IWM dist EMA200 | VIX |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OUST | 2023-12-01 | 827.67 | 1.96% | 13.76% | 1.84 | 14.31% | 6.58% | 2.65% | 12.63 |
| IOVA | 2023-01-24 | 2,250.96 | 3.73% | 10.01% | 4.56 | 13.00% | 5.51% | 1.26% | 19.20 |
| BBAI | 2023-06-13 | 3,023.17 | 3.33% | 10.05% | 1.72 | 13.04% | 9.24% | 3.55% | 14.61 |
| MVST | 2023-07-07 | 9,247.65 | 16.48% | 13.48% | 1.58 | 15.50% | 7.19% | 1.51% | 14.83 |

## Bucket feature summary

| Bucket | Trades | P&L | Win rate | Median return | O2C med | RelVol med | Intraday med | ATR med | IWM dist EMA200 med | VIX med |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 losers | 5 | -30,886.08 | 0.00% | -11.62% | 11.41% | 1.75 | 12.56% | 6.42% | 5.19% | 14.84 |
| 2023 winners | 4 | 15,349.46 | 100.00% | 3.53% | 11.77% | 1.78 | 13.68% | 6.89% | 2.08% | 14.72 |
| 2024 winners | 14 | 219,236.02 | 100.00% | 15.51% | 13.15% | 2.08 | 15.65% | 7.71% | 6.55% | 15.01 |

## Whipsaw diagnostics

| Bucket | Trades | P&L | Median return | IWM 5d return med | IWM 20d return med | IWM dist EMA200 med | 5d dist change med | VIX med | VIX 5d change med |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 losers | 5 | -30,886.08 | -11.62% | 3.76% | 8.33% | 5.19% | 3.66% | 14.84 | -0.78 |
| 2023 winners | 4 | 15,349.46 | 3.53% | 1.01% | 7.59% | 2.08% | 0.95% | 14.72 | 0.41 |
| 2024 losers | 8 | -30,106.55 | -9.88% | 0.29% | 2.08% | 7.81% | -0.06% | 13.07 | -0.26 |
| 2024 winners | 14 | 219,236.02 | 15.51% | -0.28% | 0.80% | 6.55% | -0.55% | 15.01 | -0.33 |

## Interpretazione

### 1. Non c'e' un filtro semplice tra le feature esistenti

I perdenti 2023 non hanno:

```text
relative_volume_20d chiaramente basso
VIX chiaramente alto
open_to_close_return sotto soglia in modo netto
```

Quindi aggiungere subito un filtro su volume, VIX o O2C sarebbe fragile.

### 2. Il pattern piu' chiaro e' whipsaw/melt-up IWM

I falsi positivi 2023 si concentrano quando IWM e' sopra EMA200 ma dopo un rally molto rapido:

```text
2023 losers: IWM 5d +3.76%, IWM 20d +8.33%, distance EMA200 +5.19%, 5d distance change +3.66%
2023 winners: IWM 5d +1.01%, distance EMA200 +2.08%, 5d distance change +0.95%
```

Questo conferma l'ipotesi qualitativa: EMA200 evita il bear market pieno, ma non evita i falsi rally nei regimi laterali.

### 3. Non trasformare il whipsaw in filtro adesso

Un filtro tipo:

```text
avoid if IWM 5d return too high
avoid if IWM distance EMA200 expands too fast
```

sarebbe quasi certamente overfitting macro sul 2023. Inoltre nel 2024 alcuni vincitori hanno distanza EMA200 elevata, quindi il segnale non e' universalmente negativo.

## Verdict

```text
Errore 2023 spiegabile come whipsaw/melt-up sopra EMA200, ma non abbastanza robusto per creare un nuovo filtro.
```

## Prossima mossa scelta

Procedere con OOS congelato, non Relative Strength e non nuovo macro-filter.

Run candidata:

```text
period = 2025-01-01 -> 2025-06-30
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
no ranking
no new filters
```

Ragione:

```text
Se il sistema regge in H1 2025 senza modifiche, abbiamo il primo test predittivo pulito. Se fallisce, abbiamo evidenza che 2022-2024 ha overfittato regime/periodo.
```

Relative Strength resta una futura feature di ranking, non il prossimo passo immediato.

Vedi [[2026-05-12-cascade-small-cap-ema200-regime-gate-ablation]], [[2026-05-11-cascade-small-cap-regime-diagnostics]], [[Roadmap-Master]], [[backlog]].
