---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-smoke-runs
tags: [devlog, small-cap, smoke-test, historical-run, diagnostics]
---

# 2026-05-10 - Small-Cap Smoke Runs

## Contesto

Dopo la modalita' one-shot della CLI small-cap, sono stati eseguiti due smoke run reali tramite yfinance per verificare il flusso completo da watchlist a report storico.

## Comando smoke 1

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --symbols RKLB,IONQ,SOFI,HOOD,PLTR `
  --metadata-output-path data/small_cap_metadata_smoke_20260510.csv `
  --metadata-diagnostics-path data/small_cap_metadata_smoke_20260510_diagnostics.csv `
  --output-dir experiments/runs/small_cap_smoke_20260510 `
  --start 2024-01-01 `
  --end 2024-12-31
```

## Risultato smoke 1

Metadata generati senza errori provider, ma tutti i ticker avevano market cap superiore al limite small-cap configurato di `5B`:

```text
HOOD  69.4B
IONQ  18.4B
PLTR 330.3B
RKLB  61.0B
SOFI  20.2B
```

Report:

```text
verdict: insufficient_data
rows: 1250
operational_candidates: 0
unique_symbols: 5
candidate_dates: 250
conversion_rate: 0.0
ticker_holding_window observations: 0
```

Conclusione: watchlist non coerente col filtro small-cap attuale. Utile come test negativo.

## Comando smoke 2

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --symbols LUNR,BLDE,BBAI,OPEN,OUST `
  --metadata-output-path data/small_cap_metadata_smoke2_20260510.csv `
  --metadata-diagnostics-path data/small_cap_metadata_smoke2_20260510_diagnostics.csv `
  --output-dir experiments/runs/small_cap_smoke2_20260510 `
  --start 2024-01-01 `
  --end 2024-12-31
```

## Risultato metadata smoke 2

`BLDE` e' stato escluso per metadata incompleto:

```text
BLDE,fail,missing_market_cap
```

Ticker utilizzati:

```text
BBAI 2.00B
LUNR 4.63B
OPEN 4.83B
OUST 1.60B
```

## Risultato report smoke 2

```text
verdict: beats_primary_benchmark
rows: 1000
operational_candidates: 32
unique_symbols: 4
candidate_dates: 250
conversion_rate: 0.032
strategy_proxy_return: 0.018155829167726744
primary_benchmark: equal_weight_universe
primary_benchmark_return: -0.026842843398027533
excess_return: 0.04499867256575428
```

Setup operativi:

```text
post_gap_drift: 20
breakout_continuation: 8
panic_reversal: 4
```

Benchmark:

```text
cash_flat: 0.0
IWM proxy: -0.0228047461624169
equal_weight_universe: -0.026842843398027533
random_entry_baseline: 0.023915788195949497
ticker_holding_window: 0.018155829167726744
```

## Diagnostica principale

Regime blocks:

```text
iwm_below_ema_50: 232
missing_iwm_ema_50: 196
iwm_below_ema_50;vix_above_max: 4
```

Scanner rejects dominanti:

```text
relative_volume_below_min: 756
missing_relative_volume_20d;missing_atr_pct: 48
missing_relative_volume_20d: 24
relative_volume_below_min;atr_pct_above_max: 20
gap_above_max: 17
```

## Interpretazione

Lo smoke 2 conferma che il pipeline end-to-end funziona e produce candidati operativi. Il verdict positivo non e' ancora una validazione robusta: il report e' ancora un proxy holding-window, non un portfolio backtest completo.

## Artefatti locali

Gli artefatti del report sono in `experiments/runs/...`, directory gitignored. I metadata CSV di smoke sono in `data/` e vanno trattati come artefatti generati, non come fonte canonica definitiva.

## Verification

Comandi eseguiti:

```text
python -m src.experiments.small_cap_experiment_cli ... smoke 1
python -m src.experiments.small_cap_experiment_cli ... smoke 2
```

Entrambi hanno terminato con exit code `0`.

## Prossima mossa

Prima di espandere l'universo, migliorare il report per distinguere meglio:

```text
universe rejection summary
operational-only notional
scanner reject summary normalizzata
provider metadata diagnostics
```

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-one-shot-experiment]], [[Roadmap-Master]].
