---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-rankex-trial-001-validation-result
tags: [devlog, small-cap, rankex, validation, trial-accounting]
---

# 2026-05-14 - TRIAL-RANKEX-001 validation result

## Obiettivo

Eseguire una sola validation run preconfigurata di `TRIAL-RANKEX-001` e valutare i gate pre-registrati.

## Run

```text
output_dir: experiments/runs/small_cap_rankex_trial_001_validation_2024
run_id: run_36e6d2dc2421
period: 2024-01-02..2024-12-27
config_hash: 6463e4e30dc51d5e8776bd6a6b9aa7610e41820d3f6c742e41fad4e926e53c49
```

## Risultato

```text
portfolio_return: 5.62%
total_pnl: 5616.49
trades: 100
win_rate: 47.00%
median_trade_return: -0.71%
insufficient_funds: 0
```

Benchmark portfolio-filtered:

```text
ticker_holding_window: 2.54%
random_entry_baseline: 1.94%
equal_weight_universe: 1.51%
iwm_proxy: 0.19%
```

Outlier robustness:

```text
pnl_excluding_top_1: 1189.50
sign_flip_excluding_top_1: false
pnl_excluding_top_3: -6282.54
sign_flip_excluding_top_3: true
```

## Decisione

```text
VALIDATION FAILED / STOP / NOT PROMOTED
```

Motivo:

```text
pnl_excluding_top_3 <= 0
sign_flip_excluding_top_3 = true
```

## Stato operativo

```text
NO OOS 2025
NO PAPER TRADING
NO PROMOTION
NO DISCRETIONARY SWEEP
```

Vedi [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]], [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]].
