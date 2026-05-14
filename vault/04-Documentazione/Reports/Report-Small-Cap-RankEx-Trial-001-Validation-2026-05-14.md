---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-05-14
trial_id: TRIAL-RANKEX-001
tags: [report, small-cap, ranking-exits, validation, trial-accounting]
---

# Report Small-Cap RankEx Trial 001 Validation - 2026-05-14

## Stato

```text
VALIDATION FAILED / STOP / NOT PROMOTED
```

`TRIAL-RANKEX-001` e' stato eseguito una sola volta sulla validation window pre-registrata. Non sono stati eseguiti sweep, OOS evaluation o paper trading.

## Run

```text
output_dir: experiments/runs/small_cap_rankex_trial_001_validation_2024
run_id: run_36e6d2dc2421
config_hash: 6463e4e30dc51d5e8776bd6a6b9aa7610e41820d3f6c742e41fad4e926e53c49
git_commit: fcc73afd37818a7e7310534935eb510fd9124313
period: 2024-01-02..2024-12-27
trial_id: TRIAL-RANKEX-001
candidate_run_id: null
```

Comando eseguito:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli --metadata-path data/small_cap_metadata_eligible_subset30_20260511.csv --output-dir experiments/runs/small_cap_rankex_trial_001_validation_2024 --start 2024-01-02 --end 2024-12-31 --trial-id TRIAL-RANKEX-001
```

## Policy validata

```text
small_cap_scanner_score desc
relative_volume_20d desc
open_to_close_return desc
symbol asc
```

## Summary portfolio

| Metric | Value |
|---|---:|
| Initial cash | 100000.00 |
| Ending cash | 105616.49 |
| Total P&L | 5616.49 |
| Portfolio return | 5.62% |
| Trades | 100 |
| Rejections | 82 |
| Win rate | 47.00% |
| Median trade return | -0.71% |
| Average notional | 7792.12 |
| Min cash after entry | 42194.07 |

## Benchmark comparison

Portfolio-filtered benchmark set:

| Benchmark | Return | Observations |
|---|---:|---:|
| cash_flat | 0.00% | 92 |
| iwm_proxy | 0.19% | 1 |
| equal_weight_universe | 1.51% | 30 |
| random_entry_baseline | 1.94% | 182 |
| ticker_holding_window | 2.54% | 182 |

Unfiltered benchmark set:

| Benchmark | Return | Observations |
|---|---:|---:|
| cash_flat | 0.00% | 250 |
| iwm_proxy | -2.28% | 1 |
| equal_weight_universe | 1.04% | 30 |
| random_entry_baseline | 0.84% | 7380 |
| ticker_holding_window | 2.54% | 182 |

## Outlier robustness

| Metric | Value |
|---|---:|
| Top 1 contribution | 78.82% |
| Top 3 contribution | 211.86% |
| Outlier concentration alert | true |
| P&L excluding top 1 | 1189.50 |
| Sign flip excluding top 1 | false |
| P&L excluding top 3 | -6282.54 |
| Sign flip excluding top 3 | true |
| P&L excluding top 5 | -11973.04 |
| Sign flip excluding top 5 | true |
| Best trade | ZYME 4426.99 |
| Worst trade | GDRX -3173.40 |

## Rejections and cash

```text
max_concurrent_positions: 82
insufficient_funds: 0
```

Cash starvation summary:

```text
insufficient_funds_rejections: 0
evaluable_missed_trades: 0
```

## Annual breakdown

| Year | Trades | P&L | Win rate | Median return |
|---|---:|---:|---:|---:|
| 2024 | 100 | 5616.49 | 47.00% | -0.71% |

## Setup breakdown

| Setup | Trades | Total P&L | Win rate | Median return |
|---|---:|---:|---:|---:|
| breakout_continuation | 36 | 10712.26 | 52.78% | 1.95% |
| panic_reversal | 20 | -4131.29 | 30.00% | -4.78% |
| post_gap_drift | 44 | -964.47 | 50.00% | 0.70% |

## Gate evaluation

| Gate | Result | Evidence |
|---|---|---|
| Beat ticker_holding_window | PASS | 5.62% vs 2.54% |
| Beat random_entry_baseline | PASS | 5.62% vs 1.94% |
| P&L ex-top1 positive | PASS | 1189.50 |
| P&L ex-top3 positive | FAIL | -6282.54 |
| No sign flip ex-top1/ex-top3 | FAIL | ex-top3 sign flip true |
| No single-year/regime dependency | NOT ESTABLISHED | validation window is one calendar year and top-3 dependent |
| Insufficient funds near zero | PASS | 0 insufficient_funds |
| risk_fraction unchanged | PASS | 0.01 in manifest |

## Decision

Il trial fallisce il validation gate e attiva la stop rule pre-registrata:

```text
pnl_excluding_top_3 <= 0
sign_flip_excluding_top_3 = true
```

Decisione:

```text
STOP TRIAL-RANKEX-001
NO OOS 2025
NO PAPER TRADING
NO PROMOTION
NO DISCRETIONARY SWEEP
```

## Interpretazione

Il ranking intra-candidate produce un ritorno nominale positivo e batte i benchmark principali sulla validation window, ma il risultato non e' robusto: rimuovendo i migliori tre trade il P&L diventa negativo e il segno del portfolio si inverte. Questo viola il criterio ex-topN che era esplicitamente pre-registrato per evitare promozioni basate su pochi outlier.

Vedi [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[2026-05-14-cascade-small-cap-rankex-trial-001-validation-result]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]].
