---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-temporal-split-validation
tags: [devlog, small-cap, diagnostics, temporal-split, open-to-close-return, breakout-continuation]
---

# 2026-05-11 - Small-Cap Temporal Split Validation

## Obiettivo

Validare temporalmente le soglie congelate sul filtro breakout:

```text
open_to_close_return >= 0.08
open_to_close_return >= 0.10
```

Lo scopo e' verificare se il risultato full-year sopravvive a uno split semplice H1/H2 2024, senza cambiare scanner, ranking, execution o sizing.

## Setup

Split:

```text
H1: 2024-01-02 -> 2024-06-28
H2: 2024-07-01 -> 2024-12-27
```

Config costante:

```text
allowed_setups = ["breakout_continuation"]
holding_period_bars = 5
rank_column = small_cap_scanner_score
```

Feature filters:

```text
open_to_close_return >= 0.08
open_to_close_return >= 0.10
```

## Run eseguite

```text
experiments/runs/small_cap_ablation_feature_open_to_close_008_h1_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_008_h2_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_010_h1_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_010_h2_20260511
```

Baseline full-year:

```text
experiments/runs/small_cap_ablation_feature_open_to_close_008_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_010_20260511
```

## Risultati comparativi

| Run | Trades | P&L | Return | Win rate | Median return | Top 1 % | Top 3 % | P&L ex top 1 | P&L ex top 3 | Sign flip top 3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `0.08 full` | 24 | 132,974.34 | 132.97% | 70.83% | 4.99% | 24.17% | 68.30% | 100,837.80 | 42,155.61 | false |
| `0.08 H1` | 4 | 5,625.08 | 5.63% | 75.00% | 7.28% | 137.26% | 262.38% | -2,095.81 | -9,134.27 | true |
| `0.08 H2` | 11 | 80,904.60 | 80.90% | 90.91% | 7.77% | 30.25% | 70.60% | 56,429.72 | 23,786.14 | false |
| `0.10 full` | 15 | 177,993.38 | 177.99% | 80.00% | 11.33% | 23.44% | 58.11% | 136,269.20 | 74,564.07 | false |
| `0.10 H1` | 3 | 16,658.01 | 16.66% | 100.00% | 8.50% | 51.01% | 100.00% | 8,160.80 | 0.00 | true |
| `0.10 H2` | 7 | 71,034.14 | 71.03% | 100.00% | 14.80% | 35.41% | 79.72% | 45,879.99 | 14,405.94 | false |

## Portfolio-filtered benchmark

| Run | Filtered ticker holding return | Filtered random return | Ticker obs | Random obs |
|---|---:|---:|---:|---:|
| `0.08 full` | 6.45% | 7.10% | 29 | 29 |
| `0.08 H1` | 5.40% | -2.77% | 4 | 4 |
| `0.08 H2` | 10.43% | 3.78% | 15 | 15 |
| `0.10 full` | 12.82% | 7.94% | 16 | 16 |
| `0.10 H1` | 8.94% | 7.10% | 3 | 3 |
| `0.10 H2` | 19.55% | 4.17% | 7 | 7 |

## Interpretazione

### 1. L'edge non e' uniforme nel 2024

Il risultato full-year e' trainato soprattutto da H2.

H1 ha pochissimi trade:

```text
0.08 H1: 4 trade
0.10 H1: 3 trade
```

Quindi H1 non puo' validare robustamente il filtro. Inoltre fallisce il gate ex-top3.

### 2. H2 conferma il segnale, ma con campione piccolo

`0.08 H2`:

```text
11 trade
+80.90%
win rate 90.91%
pnl_excluding_top_3 +23,786.14
sign_flip_excluding_top_3 false
filtered ticker +10.43% vs random +3.78%
```

`0.10 H2`:

```text
7 trade
+71.03%
win rate 100.00%
median return +14.80%
pnl_excluding_top_3 +14,405.94
sign_flip_excluding_top_3 false
filtered ticker +19.55% vs random +4.17%
```

Il segnale H2 e' forte, ma 7-11 trade sono pochi.

### 3. `>=0.10` resta la migliore ipotesi, non una regola live

La soglia `>=0.10` e' piu' pulita:

```text
full-year: +177.99%, 15 trade, ex-top3 +74.6k
H2: +71.03%, 7 trade, ex-top3 +14.4k
filtered benchmark H2: +19.55% vs random +4.17%
```

Ma il campione e' troppo piccolo per promozione diretta.

## Verdict

```text
OPEN_TO_CLOSE_RETURN >= 0.10 RESTA L'IPOTESI PRIMARIA, MA L'EDGE E' TIME-CONCENTRATED.
```

Questo e' un avanzamento rispetto alla sola sensitivity full-year, ma non e' ancora validazione sufficiente per paper trading o ranking definitivo.

## Rischio principale

```text
selection bias + regime concentration
```

Potremmo aver isolato un pattern reale del 2024 H2, oppure una finestra di mercato favorevole.

## Prossimo passo consigliato

Non ottimizzare altri parametri.

Sequenza consigliata:

```text
1. Estendere dati multi-year se disponibili.
2. Eseguire rolling/walk-forward con soglie congelate `>=0.08` e `>=0.10`.
3. Se `>=0.10` regge su piu' finestre, solo allora progettare ranking breakout-specifico.
4. Se non regge, trattare il filtro come regime-specific hypothesis.
```

Vedi [[2026-05-11-cascade-small-cap-open-to-close-sensitivity]], [[2026-05-11-cascade-small-cap-feature-filter-ablation]], [[Roadmap-Master]], [[backlog]].
