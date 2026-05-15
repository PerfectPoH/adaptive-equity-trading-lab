---
tipo: scaffolding-check
progetto: adaptive-equity-trading-lab
data: 2026-05-15
tags: [negative-control, scaffolding, large-cap, data-quality, governance]
---

# Report Negative Control Scaffolding Check - 2026-05-15

## Stato

```text
RESEARCH-046
SCAFFOLDING CHECK ONLY
NO TRIAL ACCOUNTING
NO STRATEGY VALIDATION
NO EDGE INTERPRETATION
TRIAL-NCTRL-001 NOT OPENED
```

Questo documento pre-dichiara ed esegue il check tecnico necessario prima di qualunque preregistrazione `TRIAL-NCTRL-001`.

## Obiettivo

Verificare che la pipeline small-cap legacy possa girare end-to-end su un universo fixed large-cap/ETF control senza modifiche strutturali e senza tuning strategico.

Il check non valuta se la strategia produce alpha. Il check valuta solo se la macchina produce artefatti coerenti su una superficie dati piu' affidabile.

## Universo baseline congelato

```text
AAPL
MSFT
NVDA
AMD
TSLA
META
AMZN
GOOGL
SPY
QQQ
```

## Config sorgente

La config del check e' committata in repo:

```text
experiments/configs/nctrl_scaffolding.py
```

Il run deve essere lanciato da quel modulo, non tramite parametri CLI estemporanei.

## Parametri modificabili e non modificabili

Modificabili solo per universe scope:

```text
SmallCapUniverseConfig.max_market_cap -> 10T
SmallCapUniverseConfig.exclude_etfs -> False
SmallCapUniverseConfig.min_market_cap -> 0
```

Non modificabili per strategy scope:

```text
SmallCapSwingScannerConfig thresholds
SmallCapExecutionConfig gap/slippage/capacity/risk assumptions
SmallCapPortfolioBacktestConfig holding period / rank / concurrency policy
MarketRegimeGuardrailConfig thresholds
```

## Outcome di successo pre-dichiarato

Lo scaffolding check passa se la pipeline gira end-to-end sui 10 ticker baseline senza eccezioni e produce artefatti coerenti:

```text
candidate_export.csv
run_manifest.json
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
small_cap_backtest_report.md
scaffolding_candidate_activity.csv
scaffolding_rejection_breakdown.csv
scaffolding_summary.json
```

Il numero di trade puo' essere zero. Generare trade non e' una regola pass/fail tecnica.

## Metriche tecniche da registrare

Il check deve registrare almeno:

```text
operational_candidates_total
avg_operational_candidates_per_day
pct_days_with_operational_candidate
rejection reasons breakdown by layer
portfolio_total_trades
artifact presence
manifest purpose
trial_accounting presence
```

Queste metriche servono a individuare rotture silenziose dell'adattamento universe-scope, non a interpretare edge.

## Manifest rule

Il `run_manifest.json` deve avere:

```text
extras.purpose = "nctrl_scaffolding_check"
extras.research_item = "RESEARCH-046"
trial_accounting = {}
```

## Stop-on-bug rule

Se durante lo scaffolding check emerge un bug latente:

```text
1. stop del check
2. backlog item dedicato
3. fix con TDD
4. rilancio solo dopo fix
```

Non si interpretano risultati prodotti da una pipeline sospetta.

## Comando previsto

```powershell
.\.venv-lab\Scripts\python.exe -m experiments.configs.nctrl_scaffolding
```

## Risultato

```text
TECHNICAL_PASS
```

Command executed:

```powershell
.\.venv-lab\Scripts\python.exe -m experiments.configs.nctrl_scaffolding
```

Output directory:

```text
experiments/runs/nctrl_scaffolding_2024_20260515
```

Run identity:

```text
run_id: run_nctrl_scaffolding_20260515
config_hash: 732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab
manifest extras.purpose: nctrl_scaffolding_check
trial_accounting_present: false
manifest period: 2024-01-02..2024-12-27
download_start: 2023-01-03
report_end: 2024-12-31
```

Artifact check:

| Artifact | Present |
|---|---:|
| `candidate_export.csv` | yes |
| `run_manifest.json` | yes |
| `portfolio_trade_log.csv` | yes |
| `portfolio_equity_curve.csv` | yes |
| `portfolio_rejections.csv` | yes |
| `portfolio_summary.csv` | yes |
| `small_cap_backtest_report.md` | yes |
| `backtest_report.md` | yes |
| `scaffolding_candidate_activity.csv` | yes |
| `scaffolding_rejection_breakdown.csv` | yes |
| `scaffolding_summary.json` | yes |

Technical metrics:

| Metric | Value |
|---|---:|
| candidate_rows | 2500 |
| candidate_days | 250 |
| operational_candidates_total | 32 |
| avg_operational_candidates_per_day | 0.128 |
| days_with_operational_candidate | 27 |
| pct_days_with_operational_candidate | 10.8% |
| portfolio_total_trades | 32 |

Rejection breakdown highlights:

| Layer | Reason | Count |
|---|---|---:|
| scanner | relative_volume_below_min | 2298 |
| scanner | gap_above_max | 7 |
| regime | iwm_below_ema_50 | 570 |
| regime | vix_above_max | 10 |

Portfolio summary is recorded only as a technical output sanity check:

```text
total_trades: 32
total_pnl: -629.02
return_pct: -0.629%
total_rejections: 0
```

This is not interpreted as strategy evidence.

## Decision

The scaffolding check passes its pre-declared technical success condition:

```text
end-to-end artifact generation without exceptions
required artifacts present
manifest purpose recorded
trial_accounting empty
large-cap/ETF universe accepted by universe-scope config only
```

This does not open `TRIAL-NCTRL-001`.

Allowed next step:

```text
write single-document TRIAL-NCTRL-001 preregistration as property-based negative control
```

Not allowed from this result alone:

```text
strategy promotion
edge claim
benchmark pass/fail claim
paper trading
small-cap trial unlock
```

Vedi [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]], [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
