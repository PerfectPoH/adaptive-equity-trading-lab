---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-report-diagnostics
tags: [devlog, small-cap, report, diagnostics, tdd]
---

# 2026-05-10 - Small-Cap Report Diagnostics

## Contesto

Dopo i primi smoke run one-shot, il report storico small-cap era tecnicamente corretto ma poco leggibile per diagnosticare perche' i ticker venivano esclusi o perche' non diventavano candidati operativi.

## Cosa e' stato migliorato

Il report small-cap ora include:

```text
universe_rejection_reasons
scanner_reject_reasons
metadata_diagnostics
metadata_diagnostic_reasons
operational_position_notional
```

## Moduli aggiornati

```text
src/analysis/small_cap_backtest_report.py
src/experiments/small_cap_historical_runner.py
src/experiments/small_cap_experiment_cli.py
```

## Markdown report

`small_cap_backtest_report.md` ora espone sezioni dedicate:

```text
## Universe Rejection Reasons
## Scanner Reject Reasons
## Metadata Diagnostics
```

Questo rende piu' leggibili casi come:

```text
market_cap_above_max
relative_volume_below_min
atr_pct_above_max
missing_market_cap
```

## Integrazione end-to-end

La diagnostica generata dal metadata builder nella modalita' one-shot viene ora inoltrata fino al report finale:

```text
write_small_cap_metadata_csv
-> run_small_cap_historical_experiment(metadata_diagnostics=...)
-> run_small_cap_historical_report(metadata_diagnostics=...)
-> write_small_cap_backtest_report_markdown(...)
```

## Test aggiunti

Sono stati aggiunti test RED/GREEN per:

```text
report builder con universe/scanner reject summaries
metadata diagnostics nel report builder
metadata diagnostics nel runner storico
metadata diagnostics nella one-shot CLI
```

## Verification

Test mirati:

```text
python -m pytest tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py tests/test_small_cap_experiment_cli.py
15 passed
```

Suite completa:

```text
python -m pytest
114 passed
```

## Impatto pratico

I prossimi smoke run sono piu' interpretabili: si distingue tra esclusioni universe, reject scanner, blocchi regime, skip execution e problemi provider metadata.

## Smoke rerun diagnostico

Eseguito rerun one-shot sulla watchlist:

```text
LUNR,BLDE,BBAI,OPEN,OUST
```

Comando:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --symbols LUNR,BLDE,BBAI,OPEN,OUST `
  --metadata-output-path data/small_cap_metadata_smoke2_diag_20260510.csv `
  --metadata-diagnostics-path data/small_cap_metadata_smoke2_diag_20260510_diagnostics.csv `
  --output-dir experiments/runs/small_cap_smoke2_diag_20260510 `
  --start 2024-01-01 `
  --end 2024-12-31
```

Output report:

```text
verdict: beats_primary_benchmark
rows: 1000
operational_candidates: 32
conversion_rate: 0.032
total_position_notional: 398219.88615000003
operational_position_notional: 290775.57105
```

Nuove sezioni verificate:

```text
Universe Rejection Reasons:
- price_below_min: 250

Scanner Reject Reasons:
- relative_volume_below_min: 776
- missing_relative_volume_20d: 76
- missing_atr_pct: 52
- atr_pct_above_max: 27
- gap_above_max: 19
- missing_previous_close: 4
- missing_gap_pct: 4

Metadata Diagnostics:
- missing_market_cap: 1
- BLDE: status=fail, reason=missing_market_cap
```

Conclusione: il report arricchito e' leggibile e distingue correttamente universe reject, scanner reject e problemi provider metadata.

## Limite ancora aperto

Il report resta un proxy holding-window: non e' ancora un portfolio backtest completo con cash allocation, overlapping positions e lifecycle ordini.

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-one-shot-experiment]], [[2026-05-10-cascade-small-cap-smoke-runs]], [[Roadmap-Master]].
