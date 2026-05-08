---
tipo: roadmap-master
progetto: adaptive-equity-trading-lab
data: 2026-05-08
ultimo-aggiornamento: 2026-05-08
tags: [roadmap, milestone, checklist, trading-lab]
---

# Master Roadmap & Checklist

## Stato sintetico

La Milestone 1 e' stata avviata con una pipeline funzionante end-to-end. I test passano, il primo esperimento e' loggato, ma la baseline 2024 non batte buy-and-hold. Questo non e' un fallimento: e' il primo risultato onesto da cui migliorare.

## Milestone 1 - MVP Core Pipeline

Obiettivo: avere una pipeline completa, riproducibile e anti-lookahead minima.

Definition of Done:

- [x] Scarica dati daily per 10 ticker.
- [x] Salva snapshot con hash.
- [x] Calcola feature point-in-time.
- [x] Crea label TP-before-SL con entry al next open.
- [x] Allena un modello baseline.
- [x] Genera segnali.
- [x] Fa backtest.
- [x] Mostra dashboard Streamlit.
- [x] Registra esperimento in CSV.
- [x] Passa test anti-lookahead minimi.
- [x] Il backtest out-of-sample su 2024 batte buy-and-hold oppure il motivo per cui non lo batte e' documentato.

Prossimi miglioramenti Milestone 1:

- [x] Rafforzare test anti-shift su backtesting.py.
- [x] Aggiungere grafico equity curve aggregata nella dashboard.
- [ ] Ripulire o archiviare `.venv` parziale se Windows lo libera.
- [x] Documentare meglio perche' la prima baseline non batte buy-and-hold.
- [x] Aggiungere analisi per simbolo: segnali, trade, skip, diagnosi.
- [x] Aggiungere conservative skip per daily-bar entry SL/TP ambiguity.
- [x] Collegare GDELT macro-news storiche 2020-2024 come feature sperimentali.

## Milestone 2 - Research Validation

- [ ] Walk-forward validation.
- [ ] TimeSeriesSplit.
- [ ] Tuning iperparametri su validation, non su test.
- [ ] Model registry con `joblib`.
- [ ] Calibration plot / reliability analysis.
- [ ] Error analyzer per trade falliti.
- [ ] Analisi soglia `model_probability` e calibrazione per ridurre collo di bottiglia.
- [ ] Notebook `04_backtest_analysis.ipynb`.
- [ ] Soglie scanner e modello versionate.

## Milestone 3 - News + Context

- [x] Primo connettore GDELT macro-news daily laggato.
- [ ] Event classifier: earnings, macro, politica, shock.
- [ ] `news_risk_filter`: block, reduce size, warning.
- [ ] Fallback se news API non risponde.
- [ ] Report su quanti trade vengono bloccati e perche'.

Vedi [[news-risk-engine]].

## Milestone 4 - Paper Trading

- [ ] Broker paper: Alpaca o IBKR.
- [ ] Modalita' signal-only.
- [ ] Modalita' paper-manual.
- [ ] Order logger.
- [ ] Slippage tracker.
- [ ] Market calendar / holidays / half days.
- [ ] Conferma manuale.
- [ ] Guardrail base.

## Milestone 5 - Realism Upgrade

- [ ] Slippage dinamico.
- [ ] Limiti volume.
- [ ] Spread checks.
- [ ] Correlation cap.
- [ ] Fiscalita' netta.
- [ ] Risk report per portafoglio.
- [ ] Data quality report.

## Milestone 6 - Institutional Validation Gate

- [ ] Dati point-in-time.
- [ ] Dataset senza survivorship bias.
- [ ] Backtester event-driven.
- [ ] Deflated Sharpe Ratio.
- [ ] Probability of Backtest Overfitting.
- [ ] Combinatorial Purged Cross-Validation.
- [ ] Dynamic market impact.
- [ ] Capacity analysis.
- [ ] HRP o allocation piu' robusta.
- [ ] Tax-aware net returns.

Possibili strumenti:

```text
Norgate / Sharadar / Databento
Nautilus Trader / QuantConnect LEAN
HRP
DSR
CPCV
```

## Milestone 7 - Small Live Manual

- [ ] No live automatico iniziale.
- [ ] Capitale piccolo.
- [ ] Conferma manuale.
- [ ] Max daily loss.
- [ ] Max weekly loss.
- [ ] Kill switch.
- [ ] No leva.
- [ ] No short iniziale.
- [ ] Audit log completo.
- [ ] Stop sempre obbligatorio.

## Regola finale

Si costruisce una fase alla volta. Se un'idea non serve alla fase corrente, va scritta nel vault e rimandata.

Vedi anche [[Architettura]], [[Memoria-AI]], [[Regole-Quant]], [[mvp-core-pipeline]].
