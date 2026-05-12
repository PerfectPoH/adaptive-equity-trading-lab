---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-portfolio-mechanics-audit
tags: [devlog, small-cap, portfolio, mechanics, sizing, cash-starvation, risk-fraction, oos]
---

# 2026-05-12 - Small-Cap Portfolio Mechanics Audit

## Obiettivo

Spiegare perche' nella run OOS full-year 2025 il portfolio perde mentre il benchmark filtrato e' positivo.

Run analizzata:

```text
experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_full_20260512
```

Regole strategiche congelate:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
```

## Artifact generati

```text
portfolio_mechanics_executed_trade_audit.csv
portfolio_mechanics_cash_starvation_audit.csv
portfolio_mechanics_day_status_audit.csv
portfolio_mechanics_filtered_candidate_status.csv
```

## Differenza chiave: benchmark vs portfolio

Il benchmark `ticker_holding_window` e' una media close-to-close equal-weight su tutti i candidati operativi del subset filtrato.

Il portfolio invece e':

```text
sequenziale
cash-constrained
position-size weighted
entry next-open con costi
soggetto a max liquidity notional
soggetto a capitale disponibile
```

Quindi il benchmark risponde a:

```text
Come performano mediamente i candidati filtrati?
```

Il portfolio risponde a:

```text
Cosa succede se li eseguo in sequenza con questa meccanica di capitale?
```

Nel 2025 full-year queste due risposte divergono.

## Filtered candidates status

| Status | Count |
|---|---:|
| executed | 15 |
| insufficient_funds | 18 |

Totale candidati filtrati:

```text
33
```

Quindi oltre meta' dei candidati filtrati non viene eseguita per mancanza di cash.

## Executed trades distribution

| Metric | Value |
|---|---:|
| Count | 15 |
| Avg return | -1.95% |
| Median return | -6.56% |
| Win rate | 33.33% |
| Total P&L | -15,906.64 |
| Dollar-weighted return | -1.32% |
| Total notional deployed | 1,204,604.27 |

## Cash-starved missed trades

| Metric | Value |
|---|---:|
| Count | 18 |
| Avg missed return | 3.50% |
| Median missed return | 4.63% |
| Missed win rate | 61.11% |
| Positive missed | 11 |
| Negative missed | 7 |
| Best missed | 33.73% |
| Worst missed | -21.73% |

Top missed winners:

| Symbol | As-of | Available cash | Missed return |
|---|---|---:|---:|
| QS | 2025-09-12 | 7.91 | 33.73% |
| SLDP | 2025-07-15 | 1.57 | 23.22% |
| ARRY | 2025-08-15 | 16.15 | 16.06% |
| ARRY | 2025-07-01 | 0.03 | 14.46% |
| MVST | 2025-09-12 | 7.91 | 14.24% |

## Key path examples

### Near-zero cash after entries

Several accepted positions leave the portfolio effectively fully invested:

```text
MVST 2025-06-16: cash_after_entry = 2.31
AMPX 2025-06-26: cash_after_entry = 0.03
IOVA 2025-07-16: cash_after_entry = 1.56
EOSE 2025-09-12: cash_after_entry = 7.91
```

This causes later valid candidates to become `insufficient_funds` rejections.

### Large losers are oversized

Worst executed trades:

| Symbol | Date | Position notional | Return | P&L | Cash after entry | Score |
|---|---|---:|---:|---:|---:|---:|
| OUST | 2025-10-14 | 134,141.18 | -23.48% | -31,498.62 | 20.97 | 83.33 |
| MVST | 2025-06-16 | 97,177.17 | -17.14% | -16,653.87 | 2.31 | 100.00 |
| EOSE | 2025-09-02 | 125,938.10 | -11.32% | -14,252.51 | 0.49 | 83.33 |
| KURA | 2025-10-27 | 102,654.28 | -10.76% | -11,042.20 | 9.26 | 100.00 |

The issue is not simply that losers exist. The issue is that losers receive very large notional allocations.

## Root cause in code

`SmallCapExecutionPlanner.plan_trade` currently computes:

```python
target_notional = min(float(available_cash), max_liquidity_notional)
position_size = math.floor(target_notional / entry_price)
```

This means the portfolio planner can deploy nearly all available cash into a single accepted trade, bounded mainly by liquidity cap.

But `SmallCapExecutionConfig` contains:

```python
risk_fraction: float = 0.01
stop_atr_multiple: float = 1.5
```

And the non-portfolio execution column path uses risk-based sizing via:

```python
calculate_position_size(equity, entry, stop, config.risk_fraction)
```

So the portfolio backtester and execution column preparer are not aligned:

```text
execution columns: risk-based sizing
portfolio planner: available-cash/liquidity sizing
```

## Diagnosis

The OOS 2025 failure is not only a strategy signal failure. It is also a portfolio mechanics failure:

1. The engine over-allocates to single names.
2. Cash is often reduced to near zero.
3. Many later filtered candidates are skipped.
4. Skipped candidates had positive average and median returns.
5. Large losers dominate the path.
6. The filtered benchmark stays positive because it is equal-weight and unconstrained by portfolio path.

## Verdict

```text
Before interpreting OOS portfolio P&L as pure strategy failure, fix/audit portfolio sizing.
```

The strategy still failed validation as executed, but the execution simulator is not institutionally acceptable yet because it ignores `risk_fraction` in the portfolio path.

## Next step

TDD change:

```text
SmallCapExecutionPlanner should respect risk_fraction-based position sizing, capped by liquidity and available cash.
```

Expected sizing logic:

```text
risk_size = calculate_position_size(available/equity basis, entry_price, stop_loss, risk_fraction)
liquidity_size = floor(max_liquidity_notional / entry_price)
cash_size = floor(available_cash / entry_price)
position_size = min(risk_size, liquidity_size, cash_size)
```

Open question for implementation:

```text
Should risk_fraction use initial_cash, current equity, or available_cash?
```

Conservative first pass:

```text
use available_cash as the risk capital basis
```

After fixing, rerun:

```text
OOS full-year 2025 frozen rules
2022-2024 multi-year frozen rules
```

Do not add filters or ranking before this mechanics fix.

Vedi [[2026-05-12-cascade-small-cap-oos-2025-full-validation]], [[2026-05-12-cascade-small-cap-oos-2025-h1-validation]], [[Roadmap-Master]], [[backlog]].
