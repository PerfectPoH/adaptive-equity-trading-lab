---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-regime-diagnostics
tags: [devlog, small-cap, diagnostics, regime, iwm, ema200, breakout-continuation]
---

# 2026-05-11 - Small-Cap Regime Diagnostics

## Obiettivo

Continuare dopo la multi-year validation 2022-2024 dell'ipotesi:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
```

Il risultato multi-year sopravviveva ex-top3, ma era chiaramente 2024-driven. Lo scopo di questo step e' aggiungere diagnostica regime passiva, senza ancora filtrare i trade.

## Implementazione

Aggiunta propagazione colonne regime in:

```text
candidate_export.csv
portfolio_trade_log.csv
portfolio_rejections.csv
```

Colonne:

```text
iwm_close
iwm_ema_50
iwm_ema_200
vix_close
```

Aggiunto artifact:

```text
portfolio_regime_profile.csv
```

E sezione report:

```text
## Regime Profile Report
```

La diagnostica e' passiva: non cambia scanner, ranking, sizing, execution o filtri.

## Test

Workflow TDD:

```text
RED: test: add passive regime diagnostics coverage
GREEN: feat: add passive regime diagnostics
```

Verifiche:

```text
pytest tests/test_small_cap_candidate_export.py tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_historical_runner.py tests/test_small_cap_backtest_report.py
50 passed

pytest
169 passed
```

## Run analizzata

```text
experiments/runs/small_cap_multiyear_open_to_close_010_2022_2024_20260511
```

Config:

```text
allowed_setups = ["breakout_continuation"]
feature_filters = [{"setup": "breakout_continuation", "feature": "open_to_close_return", "min_value": 0.10}]
period = 2022-01-03 -> 2024-12-31
```

## Risultato globale

```text
trades: 43
total_pnl: +135,069.48
return_pct: +135.07%
pnl_excluding_top_3: +44,566.65
sign_flip_excluding_top_3: false
```

Annual breakdown:

| Year | Trades | P&L | Win rate | Median return |
|---|---:|---:|---:|---:|
| 2022 | 9 | -753.52 | 44.44% | -5.95% |
| 2023 | 13 | -29,715.50 | 30.77% | -3.66% |
| 2024 | 21 | 165,538.50 | 66.67% | 8.50% |

## Regime profile

| Regime feature | Value | Trades | Avg return | Median return | Win rate | Total P&L | Avg P&L |
|---|---|---:|---:|---:|---:|---:|---:|
| iwm_above_ema_50 | True | 43 | 2.85% | 1.57% | 51.16% | 135,069.48 | 3,141.15 |
| iwm_above_ema_200 | False | 12 | -2.39% | -5.47% | 25.00% | -18,279.57 | -1,523.30 |
| iwm_above_ema_200 | True | 31 | 4.88% | 3.38% | 61.29% | 153,349.05 | 4,946.74 |
| vix_bucket | low | 22 | 1.27% | -0.53% | 45.45% | 51,747.94 | 2,352.18 |
| vix_bucket | high | 21 | 4.50% | 3.34% | 57.14% | 83,321.54 | 3,967.69 |

## Interpretazione

### 1. EMA50 non discrimina

Tutti i 43 trade avvengono con:

```text
iwm_close > iwm_ema_50
```

Quindi un gate EMA50 sarebbe ridondante sulla configurazione corrente.

### 2. EMA200 discrimina molto

Il confronto e' netto:

```text
IWM sotto EMA200: 12 trade, -18.3k P&L, win rate 25%, mediana -5.47%
IWM sopra EMA200: 31 trade, +153.3k P&L, win rate 61.29%, mediana +3.38%
```

Questo spiega parte del problema 2023: falsi breakout in regime small-cap non sufficientemente sano.

### 3. VIX non e' un filtro ovvio

Nel campione:

```text
VIX low bucket: +51.7k
VIX high bucket: +83.3k
```

Quindi non conviene introdurre un filtro VIX generico. Potrebbe eliminare trade buoni.

## Verdict

```text
IL PROSSIMO CANDIDATE GATE E' IWM ABOVE EMA200, NON VIX E NON EMA50.
```

Ma il prossimo step deve restare TDD e ablativo:

```text
allowed_setups = breakout_continuation
feature_filters = open_to_close_return >= 0.10
regime_filter = iwm_close > iwm_ema_200
```

con rejection metadata e manifest, prima di qualsiasi paper trading.

## Prossimo passo consigliato

Implementare un filtro regime configurabile e passivo:

```text
regime_filters = [
  {"feature": "iwm_close", "operator": ">", "threshold_feature": "iwm_ema_200"}
]
```

Oppure, minimo pragmatico:

```text
require_iwm_above_ema_200 = True
```

Da testare con:

```text
2022-2024 multi-year
annual breakdown
ex-top3 stress
portfolio-filtered benchmark
```

Non usare ancora VIX e non costruire ranking.

Vedi [[2026-05-11-cascade-small-cap-multiyear-validation]], [[2026-05-11-cascade-small-cap-temporal-split-validation]], [[Roadmap-Master]], [[backlog]].
