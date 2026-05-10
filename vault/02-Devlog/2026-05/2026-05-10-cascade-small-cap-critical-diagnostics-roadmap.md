---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-critical-diagnostics-roadmap
tags: [devlog, small-cap, diagnostics, roadmap, risk, portfolio]
---

# 2026-05-10 - Small-Cap Critical Diagnostics Roadmap

## Contesto

Dopo l'integrazione del portfolio backtester nel runner storico, il progetto ha superato il proxy holding-window puro: ora esistono trade log, equity curve, rejection summary e summary portfolio-aware.

Il passo successivo non deve essere aggiungere feature architetturali isolate, ma rendere falsificabile la prima equity curve di portafoglio.

## Distinzione importante

### Gia' implementato

```text
SmallCapExecutionPlanner
SmallCapPortfolioBacktester core
cash ledger
max concurrent positions
insufficient_funds
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
sezioni markdown Portfolio Backtest e Portfolio Rejection Summary
fail-closed su dati mancanti / gap / liquidita' / cash insufficiente
```

### Non ancora implementato

```text
Outlier P&L Breakdown
Score Profile Report per decili di small_cap_scanner_score
alert concentrazione top-N trade
run_id + config hash per run small-cap
survivorship sensitivity test
penalizzazione settoriale nel triage
opening regime check
random delay realistico
Deflated Sharpe Ratio
Float Rotation controller
```

Questi elementi vanno trattati come roadmap, non come stato corrente.

## Consiglio metodologico integrato

La priorita' immediata e' misurare se il portfolio return e' robusto o se dipende da pochi eventi estremi.

Sulle small-cap, una equity curve positiva puo' essere generata da pochi trade esplosivi. Questo non dimostra un edge distribuito: puo' essere una lotteria storica non replicabile.

Il secondo controllo obbligatorio e' la monotonicita' dello scanner score. Il portfolio backtester ordina i candidati giornalieri per `small_cap_scanner_score`; quindi il triage ha senso solo se score piu' alti corrispondono, out-of-sample, a performance migliori.

## Prossimo gate bloccante

Prima di nuove feature come sector cap, opening regime check o survivorship sensitivity, implementare in TDD:

```text
Portfolio Diagnostics Report
- Outlier P&L Breakdown
- Score Profile Report
- markdown sections
- CSV artifacts
```

## Metriche richieste

### Outlier P&L Breakdown

```text
total_pnl
gross_profit
top_1_pnl_contribution_pct
top_3_pnl_contribution_pct
top_5_pnl_contribution_pct
top_10_pnl_contribution_pct
max_single_trade_contribution_pct
worst_trade
best_trade
outlier_concentration_alert
```

Soglia iniziale proposta:

```text
top_3_pnl_contribution_pct > 0.40 => alert
```

### Score Profile Report

Raggruppare i trade chiusi per decili di `small_cap_scanner_score` e calcolare:

```text
trade_count
avg_return_pct
median_return_pct
win_rate
total_pnl
avg_pnl
simple_trade_sharpe
```

Obiettivo: verificare che i decili alti abbiano performance media migliore dei decili bassi. Se non c'e' monotonicita', il triage per score non aggiunge valore.

## Regola di priorita'

Non introdurre ancora penalita' settoriali o factor/correlation caps nel triage. Prima misurare il comportamento raw:

```text
raw portfolio_return
raw outlier concentration
raw score monotonicity
raw rejection_summary
```

Solo dopo si possono aggiungere controlli di diversificazione senza confondere qualita' dello score e vincoli di portafoglio.

## Relazioni

Vedi [[small-cap-swing-research-spec]], [[Roadmap-Master]], [[backlog]], [[2026-05-10-cascade-small-cap-portfolio-report-integration]], [[2026-05-10-cascade-small-cap-portfolio-backtester-core]].
