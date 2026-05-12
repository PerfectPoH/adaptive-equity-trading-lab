---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-oos-2025-h1-validation
tags: [devlog, small-cap, oos, validation, ema200, failed-gate, breakout-continuation]
---

# 2026-05-12 - Small-Cap OOS H1 2025 Validation

## Obiettivo

Eseguire il primo test realmente fuori campione con regole congelate, dopo:

1. setup ablation,
2. feature ablation,
3. temporal split,
4. multi-year 2022-2024,
5. regime diagnostics,
6. EMA200 regime gate attivo,
7. error analysis dei falsi positivi 2023.

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
experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_h1_20260512
```

Periodo richiesto:

```text
2025-01-01 -> 2025-06-30
```

Periodo risolto dal manifest:

```text
2025-01-02 -> 2025-06-26
```

Manifest filters:

```json
{
  "feature_filters": [
    {"setup": "breakout_continuation", "feature": "open_to_close_return", "min_value": 0.1}
  ],
  "regime_filters": [
    {"feature": "iwm_close", "operator": ">", "threshold_feature": "iwm_ema_200"}
  ]
}
```

## Risultato portfolio

| Metric | Value |
|---|---:|
| Trades | 2 |
| Total P&L | -16,093.19 |
| Return | -16.09% |
| Total rejections | 82 |
| P&L ex top1 | -17,353.19 |
| P&L ex top3 | -17,353.19 |
| Sign flip ex top3 | false |

Nota: `sign_flip=false` non e' positivo in questo caso, perche' il totale e' gia' negativo.

## Trade list

| Symbol | Signal date | P&L | Return | Score | O2C | RelVol20d | IWM close | IWM EMA200 | VIX |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PRCH | 2025-06-06 | 1,260.00 | 1.26% | 83.33 | 13.13% | 1.57 | 211.90 | 209.87 | 16.77 |
| MVST | 2025-06-16 | -17,353.19 | -17.14% | 100.00 | 14.89% | 1.61 | 210.77 | 210.01 | 19.11 |

## Rejections

| Reason | Count |
|---|---:|
| setup_excluded | 53 |
| feature_filtered | 19 |
| regime_filtered | 7 |
| missing_price_path | 2 |
| insufficient_funds | 1 |

## Portfolio-filtered benchmark

| Benchmark | Return | Observations |
|---|---:|---:|
| cash_flat | 0.00% | 4 |
| iwm_proxy | -1.42% | 1 |
| equal_weight_universe | 1.16% | 30 |
| random_entry_baseline | 5.43% | 3 |
| ticker_holding_window | -6.77% | 3 |

Interpretazione benchmark:

```text
Il sottoinsieme filtrato non batte random entry in OOS. Anche il proxy ticker_holding_window e' negativo.
```

## Regime profile

| Regime feature | Value | Trades | Avg return | Median return | Win rate | Total P&L |
|---|---|---:|---:|---:|---:|---:|
| iwm_above_ema_50 | True | 2 | -7.94% | -7.94% | 50.00% | -16,093.19 |
| iwm_above_ema_200 | True | 2 | -7.94% | -7.94% | 50.00% | -16,093.19 |
| vix_bucket | low | 1 | 1.26% | 1.26% | 100.00% | 1,260.00 |
| vix_bucket | high | 1 | -17.14% | -17.14% | 0.00% | -17,353.19 |

## Verdict

```text
OOS H1 2025 NON valida la strategia.
```

Motivi:

1. Sample troppo piccolo: solo 2 trade.
2. P&L negativo: -16.09%.
3. Il filtered ticker holding window e' negativo.
4. Random entry batte il subset filtrato.
5. Il trade con score 100 e O2C 14.89% e' il grande perdente, quindi score/O2C non bastano come ranking semplice.

## Implicazione metodologica

Il risultato non dimostra che l'ipotesi sia falsa in assoluto, ma blocca promozione operativa:

```text
no paper trading
no ranking production
no nuova ottimizzazione in-sample immediata
```

La strategia resta una ipotesi promettente in 2022-2024, ma non ancora validata fuori campione.

## Prossimi passi possibili

Scelte metodologicamente pulite:

1. **Broader OOS**: estendere OOS a 2025 full-year se disponibile o a finestre multiple non usate.
2. **Universe robustness**: testare un universo alternativo/simile, per ridurre survivorship e subset bias.
3. **Trial accounting / DSR**: conteggiare setup, threshold e regime gate prima di provare nuove feature.
4. **Solo dopo**: valutare Relative Strength come ranking diagnostico, non come filtro immediato.

Vedi [[2026-05-12-cascade-small-cap-2023-false-positive-error-analysis]], [[2026-05-12-cascade-small-cap-ema200-regime-gate-ablation]], [[Roadmap-Master]], [[backlog]].
