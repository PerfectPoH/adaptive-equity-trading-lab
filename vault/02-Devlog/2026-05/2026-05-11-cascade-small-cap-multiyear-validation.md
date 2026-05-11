---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-multiyear-validation
tags: [devlog, small-cap, diagnostics, multi-year, open-to-close-return, breakout-continuation]
---

# 2026-05-11 - Small-Cap Multi-Year Validation

## Obiettivo

Testare l'ipotesi primaria congelata:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
```

su un periodo piu' ampio rispetto al solo 2024, per verificare se l'edge fosse solo H2-2024 oppure se sopravvive a piu' regimi.

## Config

Download/warmup dati:

```text
2021-01-01 -> 2024-12-31
```

Periodo report:

```text
2022-01-03 -> 2024-12-31
```

Config portfolio:

```text
allowed_setups = ["breakout_continuation"]
feature_filters = [{"setup": "breakout_continuation", "feature": "open_to_close_return", "min_value": 0.10}]
holding_period_bars = 5
rank_column = small_cap_scanner_score
```

Run:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_2022_2024_20260511
```

## Risultato globale

```text
total_trades: 43
total_pnl: +135,069.48
return_pct: +135.07%
win_rate: 51.16%
median_return: +1.57%
total_rejections: 457
```

Rejections:

```text
feature_filtered: 135
setup_excluded: 310
insufficient_funds: 12
```

## Ex-outlier stress test

```text
top_1_pnl_contribution_pct: 25.34%
top_3_pnl_contribution_pct: 67.00%
pnl_excluding_top_1: +100,840.07
pnl_excluding_top_3: +44,566.65
sign_flip_excluding_top_3: false
```

Questo e' il primo gate importante: multi-year resta positivo anche togliendo i top 3 winner.

## Annual breakdown

| Period | Trades | P&L | Win rate | Median return | Top 1 % | Top 3 % | P&L ex top 1 | P&L ex top 3 | Sign flip top 3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| All | 43 | 135,069.48 | 51.16% | 1.57% | 25.34% | 67.00% | 100,840.07 | 44,566.65 | false |
| 2022 | 9 | -753.52 | 44.44% | -5.95% | n/a | n/a | -29,179.63 | -31,378.35 | false |
| 2023 | 13 | -29,715.50 | 30.77% | -3.66% | n/a | n/a | -38,963.15 | -45,551.19 | false |
| 2024 | 21 | 165,538.50 | 66.67% | 8.50% | 20.68% | 54.28% | 131,309.09 | 75,681.10 | false |

Nota: negli anni negativi, le percentuali top winner possono diventare poco interpretabili perche' il denominatore P&L totale e' negativo. Il valore utile e' il P&L assoluto per anno.

## Portfolio-filtered benchmark

Sul sottoinsieme che passa `allowed_setups` e `feature_filters`:

```text
ticker_holding_window: +4.50% su 55 osservazioni
random_entry_baseline: -0.02% su 55 osservazioni
IWM proxy: -15.17%
equal_weight_universe: -3.34%
```

Il subset filtrato batte random, IWM e universo equal-weight nel benchmark semplice close-to-close.

## Interpretazione

### 1. L'ipotesi sopravvive al multi-year ex-top3

Rispetto al temporal split solo 2024, questo e' un avanzamento sostanziale:

```text
43 trade invece di 15
+135.07% complessivo
ex-top3 ancora +44.6k
benchmark filtrato positivo vs random circa flat
```

Quindi l'ipotesi non va archiviata come puro caso H2-2024.

### 2. Ma l'edge resta 2024-driven

Breakdown per anno:

```text
2022: circa flat (-753)
2023: negativo (-29.7k)
2024: molto positivo (+165.5k)
```

Questo significa che il sistema non e' ancora una regola universale. Sembra piu' una regola di partecipazione a regimi small-cap favorevoli.

### 3. 2023 e' il warning principale

Nel 2023 il filtro produce:

```text
13 trade
-29.7k P&L
win rate 30.77%
median return -3.66%
```

Quindi la regola `>=0.10` non basta da sola a evitare falsi breakout in un regime laterale/sfavorevole.

## Verdict

```text
OPEN_TO_CLOSE_RETURN >= 0.10 SOPRAVVIVE AL MULTI-YEAR, MA RICHIEDE REGIME GATING.
```

Non e' piu' solo una micro-ipotesi H2-2024. Pero' non e' ancora una strategia live: il P&L e' dominato dal 2024 e il 2023 resta negativo.

## Prossimo passo consigliato

Non aggiungere altri filtri di prezzo/volume sul segnale.

Il prossimo gate dovrebbe essere regime-level:

```text
1. Diagnosticare performance annuale vs IWM regime columns gia' disponibili (`iwm_close`, `iwm_ema_50`, `iwm_ema_200`, `vix_close`).
2. Verificare se i trade vincenti si concentrano quando IWM e' sopra EMA50/EMA200 o quando VIX e' sotto soglia.
3. Aggiungere solo diagnostica regime passiva prima di qualsiasi filtro esecutivo.
4. Se la diagnostica e' coerente, testare un regime gate configurabile e tracciato nel manifest.
```

Vedi [[2026-05-11-cascade-small-cap-temporal-split-validation]], [[2026-05-11-cascade-small-cap-open-to-close-sensitivity]], [[Roadmap-Master]], [[backlog]].
