---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-cash-starvation-diagnostics
tags: [devlog, small-cap, portfolio, diagnostics, cash-starvation, missed-opportunity]
---

# 2026-05-11 - Small-Cap Cash Starvation Diagnostics

## Contesto

La smoke ampia su 30 ticker eleggibili ha prodotto:

```text
portfolio_return: -22.16%
total_trades: 40
total_rejections: 142
reject_reason: insufficient_funds
```

Il prossimo dubbio era metodologico: il capitale bloccato stava scartando opportunita' migliori, oppure le rejection erano in media altro rumore negativo?

## Implementazione

Aggiunta diagnostica cash starvation in:

```text
src/analysis/small_cap_portfolio_diagnostics.py
```

Nuove funzioni:

```text
build_cash_starvation_report
summarize_cash_starvation_report
```

Il report dettaglio valuta solo rejection con:

```text
reject_reason == insufficient_funds
```

Per ogni rejection valutabile calcola:

```text
symbol
as_of
entry_date
exit_date
available_cash
entry_price
exit_price
missed_return_pct
```

Metodo: next open dopo `as_of` come entry ipotetico, close dopo `holding_period_bars` come exit ipotetico. Non simula sizing ne' impatto capitale; misura solo se il trade rifiutato avrebbe avuto direzione/return interessante.

## Integrazione runner/report

`run_small_cap_historical_report` ora scrive:

```text
portfolio_cash_starvation.csv
portfolio_cash_starvation_summary.csv
```

Il markdown storico include:

```text
## Cash Starvation Diagnostics
```

## Test

Aggiunti test RED e implementazione per:

```text
cash starvation detail report
cash starvation summary
runner artifact paths
markdown section
```

Verifica mirata:

```text
python -m pytest tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py
25 passed
```

Full suite:

```text
python -m pytest
154 passed
```

## Validazione su smoke ampia

Artefatti usati:

```text
experiments/runs/small_cap_smoke_eligible_subset30_fast_20260511
```

Summary cash starvation:

```text
insufficient_funds_rejections: 142
evaluable_missed_trades: 142
avg_missed_return_pct: 0.012474861866766293
median_missed_return_pct: -0.04746003417164113
missed_win_rate: 0.38028169014084506
best_missed_symbol: MVST
best_missed_return_pct: 2.5000000837143874
worst_missed_symbol: MVST
worst_missed_return_pct: -0.3532164199290042
```

## Interpretazione

Il capitale bloccato non stava scartando in media un set chiaramente migliore:

1. `median_missed_return_pct` e' negativo: circa `-4.75%`.
2. `missed_win_rate` e' solo `38.03%`.
3. La media e' leggermente positiva (`+1.25%`) soprattutto per un outlier enorme su MVST.
4. MVST e' sia best missed trade che worst missed trade, quindi la varianza del ticker e' molto alta.

## Lettura per simbolo

Migliori missed-opportunity medie:

```text
MVST: avg +55.74%, median +6.17%, win_rate 50.00%, count 8
LUNR: avg +11.45%, median +10.41%, win_rate 75.00%, count 4
BBAI: avg +8.40%, median +6.54%, win_rate 87.50%, count 8
AEHR: avg +5.54%, median +7.12%, win_rate 80.00%, count 5
CABA: avg +5.03%, median +5.19%, win_rate 75.00%, count 4
```

Peggiori missed-opportunity medie:

```text
IOVA: avg -19.56%, count 1
CRMD: avg -13.16%, win_rate 20.00%, count 5
PRCH: avg -11.34%, win_rate 33.33%, count 3
GCT: avg -8.72%, win_rate 28.57%, count 7
QS: avg -7.90%, win_rate 0.00%, count 4
SLDP: avg -7.84%, win_rate 10.00%, count 10
```

## Verdetto

```text
NON PROMUOVERE.
```

La cash starvation non salva la strategia. Le rejection non dimostrano che il backtester stia perdendo un edge sistematico per mancanza capitale; mostrano piuttosto rumore ad alta varianza con mediana negativa.

## Implicazione metodologica

Non risolvere questo con piu' capitale o piu' concurrency. Prima va corretto il ranking/triage:

```text
small_cap_scanner_score non monotono
portfolio wide negativo
missed opportunities mediane negative
```

## Prossime azioni

1. Progettare un triage alternativo che separi setup e non tratti `small_cap_scanner_score` come score unico monotono.
2. Aggiungere diagnostica per setup-level P&L e setup-level missed opportunities.
3. Valutare se alcuni ticker/setup vanno esclusi per instabilita' solo dopo evidenza per gruppo, non con sector cap prematuro.

Vedi [[2026-05-11-cascade-small-cap-wide-smoke-diagnostics]], [[2026-05-11-cascade-small-cap-ex-outlier-stress-test]], [[Roadmap-Master]], [[backlog]].
