---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-risk-based-sizing-fix
tags: [devlog, small-cap, portfolio, sizing, risk-fraction, tdd, oos]
---

# 2026-05-12 - Small-Cap Risk-Based Sizing Fix

## Obiettivo

Correggere la distorsione emersa nel portfolio mechanics audit: il planner portfolio allocava quasi tutto il cash disponibile su un singolo trade, ignorando `risk_fraction`.

## TDD

RED test aggiunto:

```text
test_execution_planner_uses_risk_fraction_position_sizing_before_cash_or_liquidity_caps
```

Failure attesa:

```text
expected position_size = 1333
actual position_size = 2000
```

Il vecchio comportamento era guidato da liquidity/cash cap, non dal rischio.

GREEN:

```text
pytest tests/test_small_cap_execution_planner.py tests/test_small_cap_portfolio_backtester.py
20 passed

pytest
174 passed
```

## Fix

`SmallCapExecutionPlanner.plan_trade` ora usa:

```text
risk_size = calculate_position_size(available_cash, entry_price, stop_loss, risk_fraction)
liquidity_size = floor(max_liquidity_notional / entry_price)
cash_size = floor(available_cash / entry_price)
position_size = min(risk_size, liquidity_size, cash_size)
```

Base conservativa scelta:

```text
available_cash
```

Non `initial_cash` e non mark-to-market equity, per evitare over-allocation mentre il portfolio e' gia' impegnato.

## OOS rerun dopo fix

Run:

```text
experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_full_risk_sizing_20260512
```

Regole congelate:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
holding_period_bars = 5
```

## Confronto vecchio vs nuovo sizing

| Metric | Old cash/liquidity sizing | New risk sizing |
|---|---:|---:|
| Trades | 15 | 30 |
| P&L | -15,906.64 | 923.82 |
| Return | -15.91% | 0.92% |
| Ending cash | 84,093.36 | 100,923.82 |
| Insufficient funds | 18 | 0 |
| Max concurrent positions rejections | 0 | 3 |
| Avg notional | 80,306.95 | 8,532.83 |
| Min cash after entry | 0.03 | 57,968.86 |

## Benchmark invariato

| Benchmark | Return | Observations |
|---|---:|---:|
| ticker_holding_window | 3.05% | 33 |
| random_entry_baseline | 3.92% | 33 |
| iwm_proxy | -1.18% | 1 |
| equal_weight_universe | -2.22% | 30 |

## Distribuzione nuovo sizing

| Metric | Value |
|---|---:|
| Trades | 30 |
| Win rate | 46.67% |
| Avg return | 1.33% |
| Median return | -1.28% |
| P&L ex top1 | -2,700.80 |
| P&L ex top3 | -6,973.98 |
| Sign flip ex top3 | true |
| Top3 contribution | 8.55x |

## Monthly breakdown nuovo sizing

| Month | Trades | P&L | Win rate | Median return |
|---|---:|---:|---:|---:|
| 2025-01 | 1 | -1,453.88 | 0.00% | -13.54% |
| 2025-06 | 5 | -1,217.79 | 40.00% | -1.85% |
| 2025-07 | 9 | 3,223.70 | 55.56% | 2.56% |
| 2025-08 | 3 | 332.26 | 33.33% | -5.14% |
| 2025-09 | 6 | 5,210.55 | 83.33% | 9.66% |
| 2025-10 | 2 | -3,529.81 | 0.00% | -17.12% |
| 2025-11 | 1 | -1,397.44 | 0.00% | -11.41% |
| 2025-12 | 3 | -243.78 | 33.33% | -4.20% |

## Interpretazione

### 1. Il fix infrastrutturale e' valido

La distorsione di cash starvation sparisce:

```text
insufficient_funds: 18 -> 0
avg notional: 80.3k -> 8.5k
min cash after entry: 0.03 -> 57,968.86
```

Il portfolio ora puo' eseguire quasi tutti i candidati filtrati invece di bloccarli per cash.

### 2. Il P&L OOS migliora drasticamente

```text
-15.91% -> +0.92%
```

Questo conferma che la vecchia run OOS non era interpretabile come pura strategia: era contaminata da sizing/path.

### 3. La strategia resta non validata

Il risultato positivo e' fragile:

```text
pnl_excluding_top_1 = -2.7k
pnl_excluding_top_3 = -7.0k
sign_flip_excluding_top_3 = true
```

Inoltre il portfolio resta sotto:

```text
ticker_holding_window +3.05%
random_entry_baseline +3.92%
```

Quindi il fix migliora la meccanica ma non autorizza ranking o paper trading.

## Verdict

```text
Risk-based sizing fix promosso.
Strategy validation ancora non superata.
```

## Prossimo passo

Rerun comparativo con nuovo sizing su:

```text
2022-2024 multi-year EMA200 gate
```

Obiettivo:

```text
separare quanto del vecchio +169% era edge segnale e quanto era leverage/path da sizing quasi all-in.
```

Blocco ancora valido:

```text
no paper trading
no ranking production
no nuovi filtri
```

Vedi [[2026-05-12-cascade-small-cap-portfolio-mechanics-audit]], [[2026-05-12-cascade-small-cap-oos-2025-full-validation]], [[Roadmap-Master]], [[backlog]].
