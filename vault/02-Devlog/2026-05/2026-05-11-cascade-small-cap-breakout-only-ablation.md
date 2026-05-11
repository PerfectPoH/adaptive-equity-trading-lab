---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-breakout-only-ablation
tags: [devlog, small-cap, diagnostics, ablation, breakout-continuation, setup-disentangler]
---

# 2026-05-11 - Small-Cap Breakout-Only Setup Ablation

## Obiettivo

Testare in modo configurabile l'ipotesi emersa dal setup disentangler:

```text
post_gap_drift e panic_reversal non devono competere nel triage corrente;
breakout_continuation e' il solo setup candidato a ulteriore studio.
```

La modifica resta passiva/diagnostica: non cambia scanner, ranking, sizing o execution. Aggiunge solo un filtro configurabile di portafoglio.

## Implementazione

Aggiunto in `SmallCapPortfolioBacktestConfig`:

```text
allowed_setups: tuple[str, ...] | None = None
```

Comportamento:

```text
None => nessuna ablation, comportamento baseline
("breakout_continuation",) => accetta solo breakout_continuation
```

I candidati esclusi vengono registrati nei rejection log come:

```text
reject_reason = setup_excluded
```

Il flag entra automaticamente nel `run_manifest.json` perche' fa parte della dataclass di config.

## Test

Workflow TDD:

```text
RED: test: add setup ablation coverage
GREEN: feat: add setup ablation filter
```

Verifiche:

```text
pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_historical_runner.py
17 passed

pytest
162 passed
```

## Run validativa

Run:

```text
experiments/runs/small_cap_ablation_breakout_only_20260511
```

Config portfolio:

```text
allowed_setups = ["breakout_continuation"]
holding_period_bars = 5
rank_column = small_cap_scanner_score
```

Manifest conferma:

```text
config.portfolio.allowed_setups = ["breakout_continuation"]
```

## Risultati principali

### Portfolio summary

```text
initial_cash: 100,000
ending_cash: 137,967.53
total_pnl: +37,967.53
return_pct: +37.97%
total_trades: 38
total_rejections: 134
```

Rejection summary:

```text
setup_excluded: 116
insufficient_funds: 18
```

Il filtro libera capitale e consente molti piu' breakout rispetto alla run mista precedente.

### Setup summary

```text
breakout_continuation: 38 trade, total_pnl +37,967.53, avg_return +1.21%, median_return -1.69%, win_rate 47.37%
```

Interpretazione: la tesi breakout-only migliora molto il portafoglio aggregato, ma la mediana resta negativa e il win rate resta sotto il 50%.

## Ex-outlier stress test

```text
total_pnl: +37,967.53
gross_profit: +122,033.83
gross_loss: -84,066.30

top_1_pnl_contribution_pct: 63.36%
top_3_pnl_contribution_pct: 152.36%
outlier_concentration_alert: true

pnl_excluding_top_1: +13,910.24
portfolio_return_excluding_top_1: +13.91%
sign_flip_excluding_top_1: false

pnl_excluding_top_3: -19,880.92
portfolio_return_excluding_top_3: -19.88%
sign_flip_excluding_top_3: true
```

Questo e' il punto critico: breakout-only e' molto meglio della baseline, ma non supera ancora il gate anti-outlier. I top 3 winner sono necessari per mantenere la strategia positiva.

Best/worst:

```text
best_trade_symbol: LUNR, best_trade_pnl +24,057.29
worst_trade_symbol: CRMD, worst_trade_pnl -20,023.37
```

## Score profile breakout-only

```text
score 83.33: 35 trade, total_pnl +20,202.80, avg_return +0.78%, median -2.49%, win_rate 45.71%
score 100:    3 trade, total_pnl +17,764.73, avg_return +6.23%, median +5.37%, win_rate 66.67%
```

Nota metodologica: nella breakout-only run lo score 100 migliora rispetto alla run mista precedente, ma il campione e' di soli 3 trade. Non basta per riabilitare lo score universale.

## Feature profile breakout-only

### open_to_close_return

```text
Q4: 12.39% -> 18.48%, 9 trade, +42,938.84 P&L, avg_return +7.96%, median +8.50%, win_rate 77.78%
Q3:  8.45% -> 11.45%, 10 trade, +19,182.78 P&L, avg_return +4.23%, median +5.18%, win_rate 60.00%
Q2:  4.87% ->  8.42%, 9 trade, -20,906.93 P&L, avg_return -4.64%, median -5.87%, win_rate 22.22%
Q1:  0.81% ->  4.34%, 10 trade, -3,247.16 P&L, avg_return -2.63%, median -4.20%, win_rate 30.00%
```

Questa e' la miglior evidenza feature-level: breakout con forte candela intraday positiva e' la regione piu' promettente.

### intraday_range_pct

```text
Q3: 10.98% -> 12.91%, 10 trade, +46,739.67 P&L, avg_return +7.97%, median +6.91%, win_rate 60.00%
Q4: 13.80% -> 21.53%, 9 trade, +23,673.10 P&L, avg_return +1.45%, median +5.37%, win_rate 66.67%
Q2:  8.39% -> 10.91%, 9 trade, -38,368.10 P&L, avg_return -4.56%, median -5.87%, win_rate 33.33%
Q1:  3.31% ->  8.28%, 10 trade, +5,922.85 P&L, avg_return -0.58%, median -3.56%, win_rate 30.00%
```

Range medio-alto sembra utile; range intermedio basso e' tossico.

### relative_volume_20d

```text
Q4: 2.40 -> 3.51, 9 trade, +37,092.14 P&L, avg_return +3.74%, win_rate 55.56%
Q3: 1.90 -> 2.36, 10 trade, +24,019.31 P&L, avg_return +1.83%, win_rate 50.00%
Q2: 1.69 -> 1.88, 9 trade, -19,824.82 P&L, avg_return -3.34%, win_rate 33.33%
Q1: 1.51 -> 1.66, 10 trade, -3,319.10 P&L, avg_return +2.39%, win_rate 50.00%
```

Volume alto aiuta, ma non basta da solo.

## Verdict

```text
BREAKOUT-ONLY MIGLIORA IL SISTEMA, MA NON E' ANCORA PROMUOVIBILE.
```

Ragione:

```text
+37.97% nominale
ma sign_flip_excluding_top_3 = true
mediana trade negativa
win rate sotto 50%
```

Quindi la tesi corretta non e': "abbiamo trovato la strategia".

La tesi corretta e':

```text
breakout_continuation e' l'unico setup su cui vale la pena costruire un ranking specifico;
post_gap_drift e panic_reversal vanno esclusi dal triage competitivo corrente.
```

## Prossimo passo consigliato

Rule ablation passiva dentro breakout_continuation, non paper trading:

```text
open_to_close_return in Q3/Q4
intraday_range_pct in Q3/Q4
relative_volume_20d in Q3/Q4
```

Domanda da rispondere:

```text
Il breakout filtrato per feature resta positivo senza top 3 winner?
```

Solo se la risposta e' si', ha senso costruire un ranking dedicato o discutere paper trading.

Vedi [[2026-05-11-cascade-small-cap-setup-feature-diagnostics]], [[2026-05-11-cascade-small-cap-setup-disentangler-diagnostics]], [[Roadmap-Master]], [[backlog]].
