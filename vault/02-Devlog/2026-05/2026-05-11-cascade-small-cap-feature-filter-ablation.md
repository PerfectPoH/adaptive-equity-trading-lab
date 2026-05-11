---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-feature-filter-ablation
tags: [devlog, small-cap, diagnostics, ablation, feature-filters, breakout-continuation]
---

# 2026-05-11 - Small-Cap Feature Filter Ablation

## Obiettivo

Proseguire dopo la run breakout-only:

```text
breakout_continuation e' l'unico setup ancora vivo,
ma breakout-only resta outlier-driven.
```

Scopo: testare filtri feature-level passivi dentro `breakout_continuation`, senza cambiare scanner, ranking, sizing o execution.

## Scelta metodologica

Non sono stati implementati `allowed_quartiles` calcolati runtime, perche' i quartili della feature profile sono diagnostici ex-post e dipendono dalla run.

Sono stati implementati filtri a soglia esplicita:

```text
feature_filters = (
  {"setup": "breakout_continuation", "feature": "open_to_close_return", "min_value": 0.084459},
)
```

Vantaggi:

```text
- riproducibili nel manifest
- confrontabili fra run
- non dipendono da bucket ex-post ricalcolati
```

## Implementazione

Aggiunto in `SmallCapPortfolioBacktestConfig`:

```text
feature_filters: tuple[dict[str, Any], ...] | None = None
```

Comportamento:

```text
None => nessun filtro feature
setup specificato => filtro applicato solo a quel setup
setup vuoto => filtro globale
min_value/max_value => bounds numerici inclusivi lato accettazione
missing/non numeric value => fail-closed, candidate filtrato
```

I candidati esclusi vengono registrati in `portfolio_rejections.csv` con:

```text
reject_reason = feature_filtered
filter_setup
filter_feature
filter_value
filter_min_value
filter_max_value
```

Il manifest registra i filtri perche' fanno parte della dataclass config.

## Test

Workflow TDD:

```text
RED: test: add feature filter ablation coverage
GREEN: feat: add feature filter ablation
```

Verifiche:

```text
pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_historical_runner.py
19 passed

pytest
164 passed
```

## Soglie testate

Soglie derivate dai bucket Q3/Q4 della run breakout-only:

```text
open_to_close_return >= 0.084459
intraday_range_pct >= 0.109804
relative_volume_20d >= 1.896297
```

Tutte le run mantengono:

```text
allowed_setups = ["breakout_continuation"]
holding_period_bars = 5
rank_column = small_cap_scanner_score
```

## Run eseguite

```text
experiments/runs/small_cap_ablation_feature_combo_q3q4_20260511
experiments/runs/small_cap_ablation_feature_open_to_close_q3q4_20260511
experiments/runs/small_cap_ablation_feature_intraday_range_q3q4_20260511
experiments/runs/small_cap_ablation_feature_relative_volume_q3q4_20260511
```

Baseline di confronto:

```text
experiments/runs/small_cap_ablation_breakout_only_20260511
```

## Risultati comparativi

| Run | Trades | P&L | Return | Top 1 % | Top 3 % | P&L ex top 1 | P&L ex top 3 | Sign flip top 3 | Feature filtered | Cash rejects |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| breakout_only | 38 | 37,967.53 | 37.97% | 63.36% | 152.36% | 13,910.24 | -19,880.92 | true | 0 | 18 |
| combo_q3q4 | 8 | 24,413.18 | 24.41% | 98.54% | 193.60% | 355.90 | -22,849.60 | true | 45 | 3 |
| open_to_close_q3q4 | 22 | 140,771.38 | 140.77% | 24.18% | 67.32% | 106,737.96 | 46,006.27 | false | 30 | 4 |
| intraday_range_q3q4 | 18 | 114,563.25 | 114.56% | 31.07% | 81.37% | 78,965.07 | 21,337.90 | false | 32 | 6 |
| relative_volume_q3q4 | 15 | 16,356.80 | 16.36% | 147.08% | 372.59% | -7,700.49 | -44,587.36 | true | 32 | 9 |

## Interpretazione

### 1. `open_to_close_return` e' il filtro piu' forte

```text
22 trade
+140.77% return
win rate 72.73%
median return +5.71%
pnl excluding top 3 +46,006.27
sign_flip_excluding_top_3 = false
```

Questo e' il primo risultato che supera il problema principale della breakout-only: resta positivo anche senza i top 3 winner.

Non elimina del tutto la concentrazione:

```text
top_3_pnl_contribution_pct = 67.32%
```

Ma cambia la qualita' del sistema: non e' piu' sostenuto solo da tre outlier.

### 2. `intraday_range_pct` e' utile ma meno pulito

```text
18 trade
+114.56% return
win rate 61.11%
median return +4.35%
pnl excluding top 3 +21,337.90
sign_flip_excluding_top_3 = false
```

Conferma che l'espansione intraday conta. Tuttavia la concentrazione resta piu' alta:

```text
top_3_pnl_contribution_pct = 81.37%
```

### 3. Il filtro combinato e' troppo restrittivo

```text
8 trade
+24.41% return
pnl excluding top 3 -22,849.60
sign_flip_excluding_top_3 = true
```

Applicare insieme tutti e tre i filtri riduce troppo il campione e torna a dipendere da pochi outlier.

### 4. `relative_volume_20d` non basta da solo

```text
15 trade
+16.36% return
pnl excluding top 1 -7,700.49
pnl excluding top 3 -44,587.36
sign_flip_excluding_top_3 = true
```

Volume elevato puo' essere feature ausiliaria, ma non e' un filtro standalone robusto.

## Verdict

```text
OPEN_TO_CLOSE_RETURN E' IL PRIMO FILTRO BREAKOUT CHE RESTA POSITIVO SENZA TOP 3 WINNER.
```

Questa e' una svolta rispetto alla breakout-only baseline.

Tuttavia non e' ancora sufficiente per paper trading:

```text
- soglie ancora in-sample
- top 3 contribution ancora 67.32%
- benchmark random sullo stesso sottoinsieme non ancora integrato nel runner
- necessita validazione out-of-sample o walk-forward
```

## Prossimo passo consigliato

Non costruire ancora un nuovo score complesso.

Sequenza consigliata:

```text
1. Promuovere `open_to_close_return >= 0.084459` a ipotesi primaria breakout.
2. Aggiungere diagnostica benchmark sul sottoinsieme filtrato, non solo sul candidate export pre-filtro.
3. Testare soglia robusta arrotondata, es. `open_to_close_return >= 0.08` o `>= 0.10`, come sensitivity non ottimizzata.
4. Solo dopo, valutare ranking breakout-specifico.
```

Vedi [[2026-05-11-cascade-small-cap-breakout-only-ablation]], [[2026-05-11-cascade-small-cap-setup-feature-diagnostics]], [[Roadmap-Master]], [[backlog]].
