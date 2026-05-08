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
- Split temporale, niente random split.
- Label builder separato.
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
  -> Signal Engine
  -> Risk Manager
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

Limiti: non point-in-time, survivorship bias, qualita' dati non istituzionale, risultati non sufficienti per capitale reale.

## Label

```text
features al close di oggi
segnale dopo close
entry al next open
stop_loss = entry - 1.5 ATR
take_profit = entry + 3 ATR
timeout = 10 trading days
```

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

Completa in prima versione. Il primo test out-of-sample 2024 non batte buy-and-hold. Questo e' documentato, quindi la Definition of Done resta soddisfatta.

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
