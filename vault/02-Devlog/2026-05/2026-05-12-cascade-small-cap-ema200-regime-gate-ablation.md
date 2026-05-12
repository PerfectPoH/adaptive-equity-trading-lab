---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-ema200-regime-gate-ablation
tags: [devlog, small-cap, regime-filter, ema200, ablation, breakout-continuation]
---

# 2026-05-12 - Small-Cap EMA200 Regime Gate Ablation

## Obiettivo

Trasformare la diagnostica regime passiva in un filtro regime attivo e configurabile, senza introdurre ranking o paper trading.

Ipotesi congelata:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime gate = iwm_close > iwm_ema_200
```

## Implementazione

Aggiunto supporto generico in `SmallCapPortfolioBacktestConfig`:

```python
regime_filters=(
    {"feature": "iwm_close", "operator": ">", "threshold_feature": "iwm_ema_200"},
)
```

Il filtro agisce nel backtester prima dell'execution planning:

```text
reject_reason = regime_filtered
```

Metadati salvati in `portfolio_rejections.csv`:

```text
regime_filter_feature
regime_filter_operator
regime_filter_value
regime_filter_threshold_feature
regime_filter_threshold_value
```

Il filtro entra anche in:

```text
portfolio_filtered_candidate_export.csv
portfolio_filtered_benchmark_report.csv
run_manifest.json
```

## Test

Workflow TDD:

```text
RED: test: add regime filter coverage
GREEN: feat: add configurable regime filters
```

Verifiche:

```text
pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_historical_runner.py
26 passed

pytest
173 passed
```

## Run confrontate

Baseline passiva precedente:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_2022_2024_20260511
```

EMA200 gate attivo:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_20260511
```

Manifest gate:

```json
[{"feature": "iwm_close", "operator": ">", "threshold_feature": "iwm_ema_200"}]
```

## Risultato globale

| Run | Trades | P&L | Return | P&L ex top1 | P&L ex top3 | Sign flip ex top3 |
|---|---:|---:|---:|---:|---:|---|
| Baseline | 43 | 135,069.48 | 135.07% | 100,840.07 | 44,566.65 | false |
| EMA200 gate | 33 | 169,213.93 | 169.21% | 129,171.00 | 67,465.86 | false |

Delta:

```text
P&L: +34,144.45
Return: +34.14 percentage points
P&L ex top3: +22,899.21
```

## Rejections

Baseline:

| Reason | Count |
|---|---:|
| feature_filtered | 135 |
| insufficient_funds | 12 |
| setup_excluded | 310 |

EMA200 gate:

| Reason | Count |
|---|---:|
| feature_filtered | 135 |
| insufficient_funds | 8 |
| regime_filtered | 14 |
| setup_excluded | 310 |

Nota: i `regime_filtered` sono candidate-level rejections. Il numero non coincide necessariamente con i 12 trade perdenti osservati nella diagnostica passiva, perche' il filtro attivo cambia il path del capitale e quindi quali trade successivi possono entrare.

## Annual breakdown

| Year | Baseline trades | Baseline P&L | EMA200 trades | EMA200 P&L |
|---|---:|---:|---:|---:|
| 2022 | 9 | -753.52 | 2 | -4,378.91 |
| 2023 | 13 | -29,715.50 | 9 | -15,536.63 |
| 2024 | 21 | 165,538.50 | 22 | 189,129.47 |

Interpretazione:

```text
Il gate EMA200 migliora molto il totale e riduce il danno 2023, ma non elimina completamente la perdita nei regimi 2022/2023.
```

Quindi non e' ancora una prova di strategia matura per paper trading.

## Portfolio-filtered benchmark

EMA200 gate:

| Benchmark | Return | Observations |
|---|---:|---:|
| cash_flat | 0.00% | 38 |
| iwm_proxy | -11.05% | 1 |
| equal_weight_universe | 11.93% | 30 |
| random_entry_baseline | 4.16% | 41 |
| ticker_holding_window | 5.42% | 41 |

Il filtered ticker holding window batte random entry, ma il margine e' molto piu' piccolo rispetto al P&L del portfolio. Questo conferma che parte del risultato dipende ancora da path, sizing e disponibilita' di capitale.

## Regime profile dopo filtro attivo

| Regime feature | Value | Trades | Avg return | Median return | Win rate | Total P&L |
|---|---|---:|---:|---:|---:|---:|
| iwm_above_ema_50 | True | 33 | 3.72% | 3.34% | 57.58% | 169,213.93 |
| iwm_above_ema_200 | True | 33 | 3.72% | 3.34% | 57.58% | 169,213.93 |
| vix_bucket | low | 17 | 2.24% | 1.96% | 52.94% | 75,189.19 |
| vix_bucket | high | 16 | 5.30% | 3.55% | 62.50% | 94,024.74 |

Il filtro funziona: tutti i trade finali sono sopra EMA200.

## Verdict

```text
EMA200 gate promosso come filtro ablativo utile, ma non come via libera al paper trading.
```

Motivi:

1. Migliora P&L totale, P&L ex-top1 ed ex-top3.
2. Non produce sign flip dopo rimozione top3.
3. Riduce il danno 2023.
4. Resta comunque negativo in 2022 e 2023.
5. L'edge resta fortemente 2024-driven.

## Prossimo passo consigliato

Prima di ranking o paper trading:

```text
1. Analizzare trade-level annuale sotto EMA200 gate.
2. Verificare outlier concentration per anno.
3. Preparare DSR / trial accounting includendo setup, feature threshold e regime gate.
4. Solo dopo valutare ranking intra-candidate.
```

Non introdurre VIX gate ora: anche dopo EMA200, VIX high resta migliore del bucket low.

Vedi [[2026-05-11-cascade-small-cap-regime-diagnostics]], [[2026-05-11-cascade-small-cap-multiyear-validation]], [[Roadmap-Master]], [[backlog]].
