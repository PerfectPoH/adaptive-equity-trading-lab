---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-portfolio-report-integration
tags: [devlog, small-cap, portfolio, report, runner, backtest]
---

# 2026-05-10 - Small-Cap Portfolio Report Integration

## Contesto

Dopo il core `SmallCapPortfolioBacktester`, il runner storico produceva ancora solo:

```text
candidate_export.csv
benchmark_report.csv
small_cap_backtest_report.md
```

Mancava il collegamento end-to-end tra portfolio ledger e report storico.

## Cosa e' stato integrato

`run_small_cap_historical_report` ora esegue anche:

```text
run_small_cap_portfolio_backtest(candidate_export, frames, config.portfolio)
```

## Nuovi artefatti prodotti

```text
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
```

Il dizionario restituito dal runner include anche:

```text
portfolio_backtest
paths.portfolio_trade_log
paths.portfolio_equity_curve
paths.portfolio_rejections
paths.portfolio_summary
```

## Report markdown

`build_small_cap_backtest_report` e `write_small_cap_backtest_report_markdown` accettano ora:

```text
portfolio_summary
portfolio_rejection_summary
```

Il report dict include:

```text
portfolio_summary
portfolio_return
portfolio_rejection_summary
```

Il markdown include nuove sezioni:

```text
## Portfolio Backtest
## Portfolio Rejection Summary
```

## Test TDD aggiunti

```text
test_build_small_cap_backtest_report_includes_portfolio_summary
test_small_cap_historical_runner_writes_expected_artifacts
```

La test coverage verifica:

```text
- parametri portfolio nel report
- sezioni markdown portfolio
- scrittura artefatti portfolio_*.csv
- presenza di portfolio_backtest nel risultato del runner
```

## Verification

Test mirati:

```text
python -m pytest tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py tests/test_small_cap_portfolio_backtester.py
15 passed
```

Suite completa:

```text
python -m pytest
125 passed
```

## Stato attuale

Ora il report storico small-cap ha due piani:

```text
1. proxy holding-window: ticker_holding_window
2. portfolio-aware ledger: portfolio_return
```

Questo permette di iniziare a misurare il divario tra segnale ideale e capitale reale.

## Prossima mossa

Usare il portfolio backtest nelle smoke run reali e confrontare:

```text
portfolio_return
strategy_proxy_return
equal_weight_universe
portfolio_rejection_summary
```

Vedi [[2026-05-10-cascade-small-cap-portfolio-backtester-core]], [[2026-05-10-cascade-small-cap-execution-planner-core]], [[Roadmap-Master]].
