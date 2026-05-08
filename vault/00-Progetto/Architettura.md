---
tipo: architettura
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [architettura, trading, ml, backtest, streamlit]
---

# Architettura - Adaptive Equity Trading Lab

## 1. Obiettivo tecnico

Costruire un laboratorio personale di ricerca quantitativa su azioni USA. Il sistema deve scaricare dati storici, salvare snapshot, creare feature point-in-time, aggiungere contesto macro-news laggato, scannerizzare setup, creare label TP-before-SL con entry al next open, applicare split temporale purgato, addestrare modelli baseline, calibrare probabilita' su validation, generare segnali, simulare execution/risk, backtestare, registrare esperimenti e mostrare risultati in dashboard.

Non e' un bot live. Non e' una prova di profittabilita'. La Milestone 1 serve a costruire una pipeline che non bara.

## 2. Stack MVP

- Python
- yfinance
- pandas
- numpy
- scikit-learn
- backtesting.py
- streamlit
- plotly
- pytest
- tenacity
- joblib
- python-dotenv
- GDELT DOC API come sorgente news sperimentale

## 3. Flusso del sistema

```text
Market Data
  -> Data Snapshots
  -> Feature Engineering
  -> Lagged News Context
  -> Scanner
  -> Temporal Split
  -> Label Builder
  -> ML Model
  -> Probability Calibration
  -> Signal Engine
  -> Risk Manager
  -> Execution Simulator
  -> Backtest
  -> Metrics
  -> Experiment Log
  -> Streamlit Dashboard
```

## 4. Moduli implementati

```text
src/data/downloader.py       download, retry, validazione OHLCV
src/data/snapshot.py         salvataggio CSV + sha256
src/features/indicators.py   RSI, EMA, MACD, ATR e helper
src/features/feature_pipeline.py
src/features/news_features.py
src/news/gdelt_doc.py
src/scanner/stock_scanner.py
src/models/label_builder.py
src/models/trainer.py
src/models/predictor.py
src/strategy/signal_engine.py
src/risk/risk_manager.py
src/backtest/execution.py
src/backtest/runner.py
src/backtest/metrics.py
src/pipeline.py
dashboard/app.py
```

## 5. Invarianti architetturali

- Le feature non devono usare dati futuri.
- Il segnale nasce dopo il close.
- L'entry simulata e' al next open.
- Il test set non si usa per tuning.
- Le ultime barre dei periodi vanno purgate quando la label forward supererebbe il confine temporale.
- La calibrazione probabilistica si fitta su validation-only, non su test.
- Ogni run deve avere un `run_id`.
- Ogni esperimento va scritto in `experiments/log.csv`.
- Se il backtest non batte buy-and-hold, il motivo va documentato.
- I risultati MVP non autorizzano live trading.

## 6. Dati

Fonte MVP:

```text
yfinance, daily OHLCV
```

Fonte news MVP:

```text
GDELT DOC API, macro-news daily aggregate, lag 1 giorno
```

Universo iniziale:

```text
AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ
```

Limiti noti:

- dati non point-in-time;
- survivorship bias presente;
- qualita' non istituzionale;
- dati potenzialmente instabili o ritoccati dal provider;
- fallback locale su ultimo snapshot valido quando il download fresco fallisce;
- nessuna garanzia di riproducibilita' perfetta nel lungo periodo.
- GDELT macro-news non e' news finanziaria point-in-time broker-grade.

## 7. Split temporale

```text
Train:      2020-2022
Validation: 2023
Test:       2024
Forward:    2025+
```

Nota: ogni split rimuove le ultime 10 barre per simbolo quando quelle barre avrebbero bisogno di prezzi futuri oltre il confine della label.

## 8. Dashboard

Dashboard Streamlit minimale:

- ultimo run;
- experiment log;
- metriche per ticker;
- segnali recenti;
- warning sui limiti.

## 9. Evoluzione futura

Le fasi successive aggiungono walk-forward piu' ampio, model registry, news risk filter, paper trading, slippage tracker, dati point-in-time, event-driven backtesting, Deflated Sharpe Ratio, CPCV, HRP e guardrail live.

Vedi [[Roadmap-Master]] e [[Regole-Quant]].
