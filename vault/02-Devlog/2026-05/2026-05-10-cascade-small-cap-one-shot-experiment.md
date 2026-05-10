---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-one-shot-experiment
tags: [devlog, small-cap, cli, metadata, experiment, tdd]
---

# 2026-05-10 - Small-Cap One-Shot Experiment Mode

## Contesto

Dopo metadata builder e experiment CLI separati, serviva un comando unico che partisse da una watchlist ticker, generasse il CSV metadata e lanciasse il run storico small-cap.

## Cosa e' stato aggiunto

- Test one-shot in `tests/test_small_cap_experiment_cli.py`.
- Funzione `run_small_cap_watchlist_experiment` in `src/experiments/small_cap_experiment_cli.py`.
- Modalita' CLI senza `--metadata-path`, usando `--symbols` e `--metadata-output-path`.

## Pipeline one-shot

```text
symbols
-> write_small_cap_metadata_csv
-> run_small_cap_historical_experiment
-> prepare_small_cap_historical_data
-> run_small_cap_historical_report
```

## CLI one-shot

Esempio:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --symbols RKLB,IONQ,SOFI,HOOD,PLTR `
  --metadata-output-path data/small_cap_metadata.csv `
  --metadata-diagnostics-path data/small_cap_metadata_diagnostics.csv `
  --output-dir experiments/runs/small_cap_YYYYMMDD `
  --start 2024-01-01 `
  --end 2024-12-31
```

## Modalita' ancora supportata

La modalita' precedente resta disponibile:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --metadata-path data/small_cap_metadata.csv `
  --output-dir experiments/runs/small_cap_YYYYMMDD `
  --start 2024-01-01 `
  --end 2024-12-31
```

## Testabilita'

La funzione one-shot accetta:

```text
metadata_provider
downloader
run_config
```

I test usano provider e downloader fake, quindi nessuna rete viene chiamata nella suite.

## Nota metodologica

La one-shot CLI puo' fare chiamate esterne reali a yfinance sia per metadata sia per OHLCV. Rimane research-only: non invia ordini e non esegue paper/live trading.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_experiment_cli.py
5 passed
```

## Prossima mossa

Eseguire il primo run storico reale su una watchlist ridotta e controllata, poi leggere `small_cap_backtest_report.md` e diagnostica metadata prima di espandere l'universo.

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-metadata-builder]], [[2026-05-10-cascade-small-cap-experiment-cli]], [[Roadmap-Master]].
