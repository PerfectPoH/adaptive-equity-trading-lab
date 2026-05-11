---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-portfolio-diagnostics-smoke
tags: [devlog, small-cap, portfolio, smoke, diagnostics, outlier-risk, score-profile]
---

# 2026-05-10 - Small-Cap Portfolio Diagnostics Smoke

## Setup

Smoke reale rilanciata dopo l'integrazione del Portfolio Diagnostics Report.

```text
metadata: data/small_cap_metadata_smoke2_diag_20260510.csv
symbols: LUNR,BBAI,OPEN,OUST
periodo: 2024-01-01 -> 2024-12-31
output: experiments/runs/small_cap_smoke_portfolio_diag_20260510
```

Artefatti prodotti:

```text
candidate_export.csv
benchmark_report.csv
small_cap_backtest_report.md
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
portfolio_outlier_breakdown.csv
portfolio_score_profile.csv
```

## Verification

Dopo la smoke e la correzione del bucketing sugli score duplicati:

```text
python -m pytest
132 passed
```

## Portfolio summary

```text
initial_cash: 100000.0
ending_cash: 174247.9187852936
total_pnl: 74247.91878529359
return_pct: 0.7424791878529358
total_trades: 18
total_rejections: 14
```

## Benchmark comparison

```text
cash_flat: 0.0
iwm_proxy: -0.0228047461624169
equal_weight_universe: -0.0268428433980275
random_entry_baseline: 0.0239157881959494
ticker_holding_window: 0.0181558291677267
portfolio_return: 0.7424791878529358
```

Il portfolio batte tutti i benchmark della smoke, ma il confronto non basta per promuovere la strategia.

## Outlier P&L Breakdown

```text
top_1_pnl_contribution_pct: 0.3553438851767033
top_3_pnl_contribution_pct: 1.0085731231390405
top_5_pnl_contribution_pct: 1.4328818241385894
outlier_concentration_alert: True
best_trade_symbol: OUST
best_trade_pnl: 26383.54392745056
best_trade_return_pct: 0.4228968372368717
worst_trade_symbol: OUST
worst_trade_pnl: -9879.52454059143
worst_trade_return_pct: -0.1261235994850221
```

Interpretazione: il risultato e' fortemente dipendente da pochi trade vincenti. Il top 3 supera il 100% del P&L netto perche' i trade perdenti compensano una parte rilevante dei vincitori.

Verdetto outlier:

```text
FAIL: non promuovere.
```

## Score Profile Report

La smoke ha rivelato un bug metodologico iniziale: score identici venivano divisi in bucket diversi. Corretto con bucketing sui valori score unici, cosi' trade con lo stesso `small_cap_scanner_score` restano nello stesso bucket.

Profilo corretto:

```text
Q1 score 80.0: trades=11, avg_return=0.0371379824, median_return=-0.0297029514, win_rate=0.4545, total_pnl=38900.6758
Q2 score 83.3333: trades=4, avg_return=0.0156290571, median_return=-0.0574395958, win_rate=0.25, total_pnl=11257.4512
Q3 score 100.0: trades=3, avg_return=0.1191311909, median_return=0.0386928495, win_rate=0.6667, total_pnl=24089.7919
```

Interpretazione: il bucket score 100 e' migliore del bucket 83.33, ma il campione e' troppo piccolo e non dimostra monotonicita' robusta. Il bucket 80 ha P&L totale alto perche' contiene molti piu' trade, non perche' il segnale sia necessariamente migliore.

Verdetto score:

```text
INCONCLUSIVE: non usare ancora lo score per sizing o filtri live.
```

## P&L per simbolo

```text
LUNR: trades=4, pnl=49931.091350, avg_return_pct=0.172480
BBAI: trades=8, pnl=14481.975727, avg_return_pct=-0.012388
OUST: trades=6, pnl=9834.851708, avg_return_pct=0.039602
```

Nota: OPEN non compare nel trade log finale della smoke portfolio.

## Top trade

```text
OUST 2024-03-27 -> pnl 26383.543927, return 0.422897, score 100.0
BBAI 2024-12-16 -> pnl 24443.624641, return 0.163171, score 80.0
LUNR 2024-08-15 -> pnl 24057.286767, return 0.277862, score 83.3333
LUNR 2024-11-15 -> pnl 21832.281413, return 0.184568, score 80.0
BBAI 2024-12-03 -> pnl 9671.756559, return 0.069020, score 80.0
```

## Verdetto finale

```text
NON PROMUOVERE.
```

Motivi:

1. `outlier_concentration_alert=True`.
2. `top_3_pnl_contribution_pct` sopra 100% del P&L netto.
3. Solo 18 trade chiusi.
4. Score profile non ancora robusto e non sufficientemente monotono.
5. 14 rejection per `insufficient_funds`, quindi il risultato dipende molto dal path e dall'ordine dei trade.

## Prossime azioni

1. Run manifest implementato: usare `run_manifest.json` e `config_hash` nelle prossime smoke.
2. Ex-outlier stress test implementato: senza top 3 winner il portfolio passa a -0.64%.
3. Ripetere smoke su watchlist piu' ampia e piu' periodi.
4. Solo dopo valutare sector cap, random delay, survivorship sensitivity e opening regime check.

Vedi [[Roadmap-Master]], [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-portfolio-diagnostics-report]], [[2026-05-10-cascade-small-cap-critical-diagnostics-roadmap]].
