---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-portfolio-backtester-core
tags: [devlog, small-cap, portfolio, backtest, execution, tdd]
---

# 2026-05-10 - Small-Cap Portfolio Backtester Core

## Contesto

Dopo `SmallCapExecutionPlanner`, mancava il primo ledger portfolio-aware per superare il proxy holding-window.

Il nuovo step trasforma:

```text
candidate_export + frames + initial_cash
```

in:

```text
trade_log + equity_curve + rejection_summary + summary
```

## Modulo aggiunto

```text
src/backtest/small_cap_portfolio_backtester.py
```

## Test aggiunto

```text
tests/test_small_cap_portfolio_backtester.py
```

## API

```text
SmallCapPortfolioBacktestConfig
SmallCapPortfolioBacktestResult
run_small_cap_portfolio_backtest(candidate_export, frames, config)
```

## Comportamento implementato

Il backtester core:

```text
- filtra candidati operational_candidate=True
- ordina i candidati giornalieri per small_cap_scanner_score discendente
- chiude posizioni scadute prima di valutare nuovi candidati
- usa SmallCapExecutionPlanner per size, capacity, cash e gap logic
- blocca cash all'entry
- libera cash a exit
- produce trade_log con pnl e return_pct
- produce equity_curve event-based
- produce rejection_summary
- rispetta max_concurrent_positions
```

## Test TDD aggiunti

```text
test_portfolio_backtester_opens_and_closes_trade_with_cash_ledger
test_portfolio_backtester_rejects_candidate_when_cash_is_locked
test_portfolio_backtester_releases_cash_before_later_candidate
test_portfolio_backtester_respects_max_concurrent_positions
test_portfolio_backtester_builds_equity_curve
```

## Verification mirata

```text
python -m pytest tests/test_small_cap_execution.py tests/test_small_cap_execution_planner.py tests/test_small_cap_portfolio_backtester.py
16 passed
```

## Stato attuale

Il modulo e' ancora core/minimale: non e' integrato nel report storico small-cap e non sostituisce ancora il benchmark `ticker_holding_window`.

## Prossime mosse

```text
1. Collegare il portfolio backtester al runner storico small-cap.
2. Scrivere portfolio_trade_log.csv, portfolio_equity_curve.csv e portfolio_summary.csv.
3. Aggiungere portfolio_return al markdown report.
4. Confrontare portfolio_return vs equal_weight_universe e proxy holding-window.
```

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-execution-planner-core]], [[2026-05-10-cascade-small-cap-report-diagnostics]], [[Roadmap-Master]].
