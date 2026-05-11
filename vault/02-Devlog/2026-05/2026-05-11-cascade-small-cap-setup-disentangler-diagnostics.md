---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-setup-disentangler-diagnostics
tags: [devlog, small-cap, diagnostics, setup-disentangler, scanner, triage]
---

# 2026-05-11 - Small-Cap Setup Disentangler Diagnostics

## Obiettivo

Avviare il disentangler in modalita' passiva: separare la diagnostica per setup senza modificare ranking, sizing, execution planner o logica di portafoglio.

## Mappatura

Lo scanner aveva gia' una tassonomia implicita in `small_cap_setup`:

```text
panic_reversal
breakout_continuation
post_gap_drift
```

Quindi non e' stato introdotto un enum nuovo in questa fase. Il campo esistente viene propagato nei log e usato come `setup_type` diagnostico.

## Implementazione

Aggiunto pass-through di `small_cap_setup` in:

```text
src/backtest/small_cap_portfolio_backtester.py
```

Nuove diagnostiche in:

```text
src/analysis/small_cap_portfolio_diagnostics.py
```

Funzioni:

```text
build_setup_summary_report
build_setup_score_profile_report
build_setup_cash_starvation_summary
```

Nuovi artefatti del runner storico:

```text
portfolio_setup_summary.csv
portfolio_setup_score_profile.csv
portfolio_setup_cash_starvation_summary.csv
```

Nuove sezioni markdown:

```text
## Setup Diagnostics
## Setup Score Profile Report
## Setup Cash Starvation Diagnostics
```

## Principio metodologico

Questa modifica e' diagnostics-only:

```text
non cambia candidati
non cambia sorting
non cambia sizing
non cambia execution
non cambia cash ledger
```

Serve solo a capire quale setup perde, quale guadagna e se lo score e' monotono dentro ciascun setup.

## Test

Workflow TDD:

```text
RED tests commit: test: add setup diagnostics coverage
GREEN implementation: feat: add passive setup diagnostics
```

Verifica mirata:

```text
pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py
35 passed
```

Full suite:

```text
pytest
158 passed
```

## Validazione sulla wide smoke esistente

Run:

```text
experiments/runs/small_cap_smoke_eligible_subset30_fast_20260511
```

### Setup summary

```text
breakout_continuation: trade_count 16, total_pnl +3,747.06, avg_return +2.93%, median_return +0.33%, win_rate 50.00%
panic_reversal:        trade_count 8,  total_pnl -3,148.00, avg_return -0.02%, median_return +1.37%, win_rate 50.00%
post_gap_drift:        trade_count 16, total_pnl -22,760.47, avg_return -1.19%, median_return +0.76%, win_rate 50.00%
```

Prima evidenza:

```text
post_gap_drift e' la zavorra principale del P&L realizzato.
breakout_continuation e' l'unico setup positivo nel campione.
panic_reversal e' circa piatto in return medio ma negativo in P&L.
```

### Setup score profile

```text
breakout_continuation Q1 score 83.33: total_pnl +12,354.33, avg_return +4.21%
breakout_continuation Q2 score 100:   total_pnl -8,607.27,  avg_return -6.03%

panic_reversal Q1 score 80:           total_pnl -1,852.97,  avg_return +1.06%
panic_reversal Q2 score 100:          total_pnl -1,295.04,  avg_return -3.24%

post_gap_drift Q1 score 80:           total_pnl -23,378.68, avg_return -0.50%
post_gap_drift Q2 score 100:          total_pnl +618.21,    avg_return -3.28%
```

L'evidenza importante non e' che un setup sia gia' promuovibile. E' che lo score 100 non e' monotono neanche dentro i setup principali. In breakout_continuation il bucket 83.33 batte nettamente il bucket 100.

### Setup cash starvation

```text
breakout_continuation: missed 46, avg -0.94%, median -4.23%, win_rate 43.48%
panic_reversal:        missed 24, avg -8.71%, median -8.00%, win_rate 8.33%
post_gap_drift:        missed 72, avg +5.96%, median -3.21%, win_rate 44.44%
```

Post-gap drift ha media missed positiva solo per outlier MVST, ma mediana ancora negativa. Panic reversal missed opportunities sono nettamente negative.

## Interpretazione

La diagnosi diventa piu' specifica:

```text
Il problema non e' solo score aggregato non monotono.
Il problema e' che i criteri che assegnano score massimo non ordinano bene i trade nemmeno dentro setup_type.
```

Possibile lettura:

1. `breakout_continuation` merita studio ulteriore, ma non con score attuale.
2. `post_gap_drift` e' responsabile della maggior parte della perdita realizzata.
3. `panic_reversal` non mostra edge nel campione e le missed opportunities sono pessime.
4. `small_cap_scanner_score == 100` non va usato come segnale di qualita'.

## Verdetto

```text
NON PROMUOVERE.
```

Il disentangler passivo conferma che non bisogna andare a paper trading. La prossima ricerca deve lavorare su feature/ranking per setup, partendo probabilmente da breakout_continuation, e trattare post_gap_drift come sospetto finche' non viene rispecificato.

## Prossime azioni

1. Aggiungere feature-level diagnostics per `breakout_continuation`.
2. Capire perche' score 100 peggiora: quali criteri distinguono Q2 da Q1?
3. Isolare `post_gap_drift` e verificare se le perdite dipendono da sizing/notional o da pattern strutturalmente negativo.
4. Non modificare execution/cash/sizing finche' non emerge ranking monotono per setup.

Vedi [[2026-05-11-cascade-small-cap-cash-starvation-diagnostics]], [[2026-05-11-cascade-small-cap-wide-smoke-diagnostics]], [[Roadmap-Master]], [[backlog]].
