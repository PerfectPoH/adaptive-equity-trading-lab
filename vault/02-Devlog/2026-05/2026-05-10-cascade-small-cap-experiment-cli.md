---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-experiment-cli
tags: [devlog, small-cap, cli, experiment, downloader, tdd]
---

# 2026-05-10 - Small-Cap Experiment CLI

## Contesto

Dopo data preparer e runner storico small-cap, serviva un orchestratore avviabile da comando che collegasse metadata CSV, download OHLCV, preparazione dati e report storico.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_experiment_cli.py`.
- Modulo `src/experiments/small_cap_experiment_cli.py`.
- Funzione `run_small_cap_historical_experiment`.
- Entry point `main()` con `argparse`.

## Pipeline

```text
load metadata CSV
select optional symbol subset
download OHLCV for selected symbols
download IWM proxy
download VIX optional
prepare_small_cap_historical_data(...)
run_small_cap_historical_report(...)
```

## CLI

Esempio:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli `
  --metadata-path data/small_cap_metadata.csv `
  --output-dir experiments/runs/small_cap_YYYYMMDD `
  --start 2024-01-01 `
  --end 2024-12-31 `
  --symbols AAA,BBB,CCC
```

## Argomenti

```text
--metadata-path  CSV con symbol, market_cap, is_etf
--output-dir     directory artefatti
--start          data iniziale download/esperimento
--end            data finale opzionale
--symbols        subset opzionale comma-separated
--iwm-symbol     default IWM
--vix-symbol     default ^VIX, stringa vuota per disabilitare
```

## Output

Il comando produce gli artefatti del runner storico:

```text
candidate_export.csv
benchmark_report.csv
small_cap_backtest_report.md
```

## Testabilita'

La funzione orchestratrice accetta un `downloader` iniettabile. I test usano un downloader fake per evitare rete e rendere la pipeline deterministica.

## Nota metodologica

La CLI puo' fare download esterni tramite `download_ticker`, quindi va usata consapevolmente. Il modulo resta signal/research-only: non invia ordini e non attiva paper/live trading.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_experiment_cli.py
3 passed
```

## Prossima mossa

Preparare un piccolo CSV metadata reale e lanciare il primo esperimento storico small-cap su una watchlist controllata.

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-data-preparer]], [[2026-05-09-cascade-small-cap-historical-runner]], [[Roadmap-Master]].
