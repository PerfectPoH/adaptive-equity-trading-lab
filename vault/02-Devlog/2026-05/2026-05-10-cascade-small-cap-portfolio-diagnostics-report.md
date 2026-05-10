---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-portfolio-diagnostics-report
tags: [devlog, small-cap, portfolio, diagnostics, outlier-risk, score-profile]
---

# 2026-05-10 - Small-Cap Portfolio Diagnostics Report

## Contesto

La roadmap critica richiedeva il gate bloccante prima di nuove feature portfolio:

```text
Outlier P&L Breakdown
Score Profile Report
```

L'obiettivo era trasformare la prima equity curve portfolio-aware in un esperimento falsificabile: non basta sapere il `portfolio_return`, bisogna sapere se il rendimento e' concentrato in pochi outlier e se lo scanner score discrimina davvero la qualita' dei trade.

## Modulo aggiunto

```text
src/analysis/small_cap_portfolio_diagnostics.py
```

## Test aggiunto

```text
tests/test_small_cap_portfolio_diagnostics.py
```

## Funzioni

```text
build_portfolio_outlier_breakdown(trade_log)
build_score_profile_report(trade_log)
```

## Outlier P&L Breakdown

Metriche prodotte:

```text
total_trades
total_pnl
gross_profit
gross_loss
top_1_pnl_contribution_pct
top_3_pnl_contribution_pct
top_5_pnl_contribution_pct
top_10_pnl_contribution_pct
max_single_trade_contribution_pct
outlier_concentration_alert
best_trade_symbol
best_trade_pnl
best_trade_return_pct
worst_trade_symbol
worst_trade_pnl
worst_trade_return_pct
```

Alert iniziale:

```text
top_3_pnl_contribution_pct > 0.40
```

## Score Profile Report

I trade chiusi vengono raggruppati per quantili di `small_cap_scanner_score`.

Colonne:

```text
score_bucket
min_score
max_score
trade_count
avg_return_pct
median_return_pct
win_rate
total_pnl
avg_pnl
simple_trade_sharpe
```

## Integrazione runner/report

`run_small_cap_historical_report` ora produce anche:

```text
portfolio_outlier_breakdown.csv
portfolio_score_profile.csv
```

Il dict restituito include:

```text
portfolio_outlier_breakdown
portfolio_score_profile
paths.portfolio_outlier_breakdown
paths.portfolio_score_profile
```

Il markdown include:

```text
## Portfolio Outlier Breakdown
## Score Profile Report
```

## Trade log enrichment

`SmallCapPortfolioBacktester` conserva ora `small_cap_scanner_score` nel `trade_log`, necessario per il profilo per decili.

## Verification mirata

```text
python -m pytest tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py
21 passed
```

## Prossima mossa

Eseguire smoke reale con i nuovi artefatti e confrontare:

```text
portfolio_return
strategy_proxy_return
equal_weight_universe
top_3_pnl_contribution_pct
outlier_concentration_alert
score profile deciles
```

Vedi [[2026-05-10-cascade-small-cap-critical-diagnostics-roadmap]], [[2026-05-10-cascade-small-cap-portfolio-report-integration]], [[Roadmap-Master]].
