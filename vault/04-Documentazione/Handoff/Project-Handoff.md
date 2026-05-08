---
tipo: handoff
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [handoff, progetto, agenti]
---

# Project Handoff - Adaptive Equity Trading Lab

## Nome

Adaptive Equity Trading Lab.

## Obiettivo

Costruire un laboratorio personale di trading quantitativo su azioni USA. Il sistema scarica dati storici, crea feature, scannerizza candidati, genera segnali con ML, fa backtest riproducibili, registra esperimenti e mostra risultati in dashboard.

Non e' un bot che fa soldi. E' una piattaforma di ricerca per capire se una strategia ha senso, misurare rischio, evitare bias e documentare decisioni.

## Principio guida

```text
Prototype != reliable strategy
Backtest != real trading
Paper trading != live trading
Live small != scaling
```

## Decisioni chiave

- MVP piccolo e costruibile.
- `yfinance` solo per prototipo.
- `backtesting.py` solo per MVP.
- Entry al next open.
- Split temporale purgato, niente random split.
- Label builder separato.
- Default di ricerca corrente: `random_forest`, isotonic calibration con `model_probability > 0.25`.
- Experiment log obbligatorio.
- Dashboard Streamlit minima.
- News Engine, Graphify, Paper Trading e tool avanzati fuori dalla Milestone 1.
- Vault manuale in Markdown.
- Prima del live serio serve una Institutional Validation Gate.

## Stack MVP

```text
Python
yfinance
pandas
numpy
scikit-learn
backtesting.py
streamlit
plotly
pytest
tenacity
joblib
python-dotenv
```

## Architettura MVP

```text
Market Data
  -> Data Snapshots
  -> Feature Engineering
  -> Scanner
  -> Temporal Split
  -> Label Builder
  -> ML Model
  -> Validation Calibration
  -> Signal Engine
  -> Optional Signal Quality Rank Filter
  -> Risk Manager
  -> Optional Market Exposure / Risk Fraction Adjustment
  -> Execution Simulator
  -> Backtest
  -> Metrics
  -> Experiment Log
  -> Streamlit Dashboard
```

## Comandi

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.model_comparison
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

## Dati

Fonte MVP:

```text
yfinance, daily OHLCV
```

Universo:

```text
AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ
```

Limiti: non point-in-time, survivorship bias, qualita' dati non istituzionale, risultati non sufficienti per capitale reale. Se `yfinance` fallisce, il downloader puo' usare l'ultimo snapshot locale valido per tenere stabile l'universo degli esperimenti.

## Label

```text
features al close di oggi
segnale dopo close
entry al next open
stop_loss = entry - 1.5 ATR
take_profit = entry + 3 ATR
timeout = 10 trading days
```

Le ultime 10 barre di ogni periodo temporale vengono purgate quando la label userebbe prezzi oltre il confine train/validation/test.

## Risk MVP

```text
max 1% rischio per trade
max 3 posizioni
stop obbligatorio
no averaging down
no leva
no short
```

## Milestone 1 status

Completa in prima versione. Il run corrente `20260508_200621` usa `use_news=false`, `model_type=random_forest`, feature set baseline, isotonic calibration, `model_probability > 0.25`, stop `1.5 ATR`, take-profit `3 ATR`, timeout 10 giorni, no regime filters, no daily rank filter, default risk 1% per trade. Il test out-of-sample 2024 fa circa 6.49% medio contro circa 48% buy-and-hold. Non batte il benchmark; questo e' documentato, quindi la Definition of Done resta soddisfatta.

## Milestone future

- Milestone 2: Research Validation.
- Milestone 3: News + Context.
- Milestone 4: Paper Trading.
- Milestone 5: Realism Upgrade.
- Milestone 6: Institutional Validation Gate.
- Milestone 7: Small Live Manual.

## Regola finale

Costruire solo la fase corrente. Tutto il resto va nel vault e resta in roadmap.

Vedi [[INDEX]], [[Roadmap-Master]], [[Memoria-AI]], [[Regole-Quant]].
