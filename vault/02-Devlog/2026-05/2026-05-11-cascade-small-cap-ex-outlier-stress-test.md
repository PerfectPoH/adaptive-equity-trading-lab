---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-ex-outlier-stress-test
tags: [devlog, small-cap, portfolio, diagnostics, outlier-risk, stress-test]
---

# 2026-05-11 - Small-Cap Ex-Outlier Stress Test

## Contesto

La smoke portfolio diagnostics del 2026-05-10 aveva prodotto un portfolio return molto alto:

```text
portfolio_return: 0.7424791878529358
```

ma anche un alert critico:

```text
top_3_pnl_contribution_pct: 1.0085731231390405
outlier_concentration_alert: True
```

Il prossimo controllo naturale e' misurare cosa resta del P&L togliendo i migliori trade vincenti.

## Implementazione

Esteso:

```text
src/analysis/small_cap_portfolio_diagnostics.py
```

`build_portfolio_outlier_breakdown` ora accetta:

```text
initial_cash: float | None
```

e produce metriche ex-outlier:

```text
pnl_excluding_top_1
pnl_excluding_top_3
pnl_excluding_top_5
sign_flip_excluding_top_1
sign_flip_excluding_top_3
sign_flip_excluding_top_5
portfolio_return_excluding_top_1
portfolio_return_excluding_top_3
portfolio_return_excluding_top_5
```

`run_small_cap_historical_report` passa `initial_cash` dal `portfolio_summary`, quindi gli artefatti futuri includeranno anche i return ex-outlier.

## Test

Aggiunti casi in:

```text
tests/test_small_cap_portfolio_diagnostics.py
```

Copertura:

```text
empty trade log
ex-outlier P&L senza initial_cash
portfolio_return_excluding_top_N con initial_cash
sign flip quando i top winner dominano
assenza di sign flip quando i winner sono distribuiti
```

## Verification

Mirati:

```text
python -m pytest tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_historical_runner.py tests/test_small_cap_backtest_report.py
23 passed
```

Suite completa:

```text
python -m pytest
152 passed
```

## Validazione su smoke 2026-05-10

Senza nuove chiamate dati, il trade log gia' prodotto dalla smoke `small_cap_smoke_portfolio_diag_20260510` e' stato riletto localmente.

Risultato:

```text
total_pnl: 74247.9187852936
top_1_pnl_contribution_pct: 0.3553438851767033
top_3_pnl_contribution_pct: 1.0085731231390405
pnl_excluding_top_1: 47864.37485784304
portfolio_return_excluding_top_1: 0.4786437485784304
sign_flip_excluding_top_1: False
pnl_excluding_top_3: -636.5365505638038
portfolio_return_excluding_top_3: -0.006365365505638038
sign_flip_excluding_top_3: True
pnl_excluding_top_5: -32140.574522271738
portfolio_return_excluding_top_5: -0.32140574522271737
sign_flip_excluding_top_5: True
```

## Verdetto

```text
NON PROMUOVERE.
```

Motivo: il portfolio passa da `+74.25%` a `-0.64%` togliendo i top 3 trade vincenti. Questo conferma che l'equity curve e' outlier-driven.

## Implicazione metodologica

Anche quando `portfolio_return` batte benchmark e random baseline, il setup resta bocciato se:

```text
sign_flip_excluding_top_3=True
```

Questo check deve rimanere gate bloccante prima di sizing, filtri live, sector caps o paper trading.

## Prossime azioni

1. Ripetere smoke su watchlist piu' ampia usando il run manifest gia' presente.
2. Leggere nel markdown e nel CSV generati da nuova smoke le metriche ex-outlier aggiunte al breakdown.
3. Solo dopo valutare sector cap, random delay, survivorship sensitivity e opening regime check.

Vedi [[2026-05-10-cascade-small-cap-portfolio-diagnostics-smoke]], [[2026-05-10-cascade-small-cap-portfolio-diagnostics-report]], [[Roadmap-Master]], [[backlog]].
