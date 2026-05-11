---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-open-to-close-sensitivity
tags: [devlog, small-cap, diagnostics, sensitivity, open-to-close-return, breakout-continuation]
---

# 2026-05-11 - Small-Cap Open-to-Close Sensitivity

## Obiettivo

Continuare dopo la feature filter ablation:

```text
open_to_close_return >= 0.084459
```

era il primo filtro breakout che restava positivo senza i top 3 winner, ma la soglia era ancora derivata da bucket in-sample.

Questo step testa due soglie arrotondate e piu' leggibili:

```text
open_to_close_return >= 0.08
open_to_close_return >= 0.10
```

In parallelo e' stata aggiunta diagnostica benchmark sul sottoinsieme effettivamente ammesso dal portfolio, dopo `allowed_setups` e `feature_filters`.

## Implementazione diagnostica

Aggiunto helper:

```text
filter_small_cap_portfolio_candidates(candidate_export, config.portfolio)
```

Produce il subset di candidati operativi che passano:

```text
allowed_setups
feature_filters
```

Il runner storico ora salva:

```text
portfolio_filtered_candidate_export.csv
portfolio_filtered_benchmark_report.csv
```

E il markdown report include:

```text
## Portfolio-Filtered Candidate Summary
## Portfolio-Filtered Benchmark Comparison
```

## Test

Workflow TDD:

```text
RED: test: add portfolio filtered benchmark coverage
GREEN: feat: add portfolio filtered benchmarks
```

Verifiche:

```text
pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_historical_runner.py tests/test_small_cap_backtest_report.py
29 passed

pytest
167 passed
```

## Run eseguite

```text
experiments/runs/small_cap_ablation_feature_open_to_close_008_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_010_20260511
```

Baseline precedente:

```text
experiments/runs/small_cap_ablation_feature_open_to_close_q3q4_20260511
```

## Risultati comparativi

| Run | Trades | P&L | Return | Win rate | Median return | Top 1 % | Top 3 % | P&L ex top 1 | P&L ex top 3 | Sign flip top 3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `>=0.084459` | 22 | 140,771.38 | 140.77% | 72.73% | 5.71% | 24.18% | 67.32% | 106,737.96 | 46,006.27 | false |
| `>=0.08` | 24 | 132,974.34 | 132.97% | 70.83% | 4.99% | 24.17% | 68.30% | 100,837.80 | 42,155.61 | false |
| `>=0.10` | 15 | 177,993.38 | 177.99% | 80.00% | 11.33% | 23.44% | 58.11% | 136,269.20 | 74,564.07 | false |

## Portfolio-filtered benchmark

| Run | Filtered ticker holding return | Filtered random return | Ticker observations | Random observations |
|---|---:|---:|---:|---:|
| `>=0.08` | 6.45% | 7.10% | 29 | 29 |
| `>=0.10` | 12.82% | 7.94% | 16 | 16 |

Nota: `ticker_holding_window` e' un benchmark close-to-close medio sul subset filtrato, non replica sizing, cash constraints, entry next-open o ranking del portfolio backtest.

## Interpretazione

### `>=0.08`

Risultato robusto rispetto al gate anti-outlier:

```text
24 trade
return +132.97%
win rate 70.83%
median return +4.99%
pnl excluding top 3 +42,155.61
sign_flip_excluding_top_3 = false
```

Ma il benchmark filtrato non batte il random nel semplice close-to-close:

```text
ticker_holding_window +6.45%
random_entry_baseline +7.10%
```

Questo non invalida il portfolio result, ma segnala che la soglia `0.08` puo' essere ancora troppo permissiva.

### `>=0.10`

Risultato piu' forte e piu' coerente:

```text
15 trade
return +177.99%
win rate 80.00%
median return +11.33%
pnl excluding top 3 +74,564.07
sign_flip_excluding_top_3 = false
```

Benchmark filtrato:

```text
ticker_holding_window +12.82%
random_entry_baseline +7.94%
```

Questa e' la prima soglia arrotondata che mostra superiorita' anche nel benchmark filtrato semplice.

## Verdict

```text
open_to_close_return >= 0.10 e' la migliore ipotesi primaria, ma resta sample-small.
```

Il risultato e' piu' convincente di `>=0.084459` e `>=0.08`, pero' ha solo 15 trade. Non va promosso a live rule prima di validazione fuori campione.

## Prossimo passo consigliato

Non costruire ancora un ranking complesso.

Sequenza consigliata:

```text
1. Congelare due candidate rules: >=0.08 come permissiva, >=0.10 come selettiva.
2. Eseguire validazione walk-forward o split temporale: first half fit / second half validation.
3. Se `>=0.10` regge fuori campione, valutare ranking breakout-specifico basato su open_to_close_return.
4. Se non regge, trattare il risultato come in-sample artifact.
```

Vedi [[2026-05-11-cascade-small-cap-feature-filter-ablation]], [[2026-05-11-cascade-small-cap-breakout-only-ablation]], [[Roadmap-Master]], [[backlog]].
