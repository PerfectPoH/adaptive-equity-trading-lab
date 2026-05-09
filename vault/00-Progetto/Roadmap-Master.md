---
tipo: roadmap-master
progetto: adaptive-equity-trading-lab
data: 2026-05-08
ultimo-aggiornamento: 2026-05-08
tags: [roadmap, milestone, checklist, trading-lab]
---

# Master Roadmap & Checklist

## Stato sintetico

La Milestone 1 e' una pipeline funzionante end-to-end. Il default corrente usa Random Forest, universo completo da 10 simboli, feature baseline, calibrazione isotonic, soglia `model_probability > 0.25`, stop `1.5 ATR`, take-profit `3 ATR`, timeout 10 giorni, nessun filtro ranking giornaliero e rischio default 1% per trade. Dopo timeout-consistent backtesting e finalizzazione dei trade a fine finestra, il backtest 2024 fa circa 6.49%, ma resta sotto buy-and-hold: risultato utile, non strategia pronta. La baseline large-cap ML e' ora congelata come controllo negativo; la nuova research track proposta e' long-only small/mid-cap swing.

## Milestone 1 - MVP Core Pipeline

Obiettivo: avere una pipeline completa, riproducibile e anti-lookahead minima.

Definition of Done:

- [x] Scarica dati daily per 10 ticker.
- [x] Salva snapshot con hash.
- [x] Calcola feature point-in-time.
- [x] Crea label TP-before-SL con entry al next open.
- [x] Purga le ultime barre di ogni split se la label forward supererebbe il confine temporale.
- [x] Allena un modello baseline.
- [x] Calibra probabilita' su validation-only.
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
- [x] Eseguire news ablation con/senza GDELT.
- [x] Eseguire threshold validation ampia `0.45`-`0.60`.
- [x] Aggiungere fallback agli snapshot locali quando `yfinance` fallisce.

## Milestone 2 - Research Validation

- [x] Walk-forward validation iniziale.
- [x] TimeSeriesSplit.
- [x] Tuning iperparametri su validation, non su test.
- [x] Model registry con `joblib`.
- [x] Calibration report / reliability analysis iniziale.
- [x] Trade-level export e prima error analysis.
- [x] Prima analisi soglia `model_probability`: default sperimentale portato a `0.55`.
- [x] Walk-forward threshold selection: default aggiornato a `0.45`.
- [x] Walk-forward raw vs isotonic: default aggiornato a isotonic `0.25`.
- [x] Model comparison iniziale: logistic regression vs random forest vs hist gradient boosting.
- [x] Calibration plot / probability calibration vera.
- [x] Implementare calibration layer su validation-only.
- [x] Trade-level feature regime analysis.
- [x] Regime-filter validation su volume, distance-from-high e ATR%.
- [x] Backtest threshold piu' ampio: 0.45-0.70 con selection su validation.
- [ ] Valutare combined filters solo come modalita' risk-first dopo walk-forward.
- [ ] Aggiungere fold walk-forward ulteriori quando ci saranno piu' anni/dati migliori.
- [x] Aggiungere embargo esplicito ai temporal split/walk-forward fold.
- [x] Feature upgrade controllato dopo model comparison: enhanced context testato, non promosso.
- [x] Target/exit comparison: timeout coerente nel backtest, varianti ATR testate, nessuna promossa.
- [x] Signal-quality/ranking comparison: top-N giornaliero testato, nessuna variante promossa.
- [x] Market-exposure comparison: 1%, 1.5%, 2% e risk scaling SPY testati, nessuna variante promossa.
- [x] Universe-selection comparison: top-N validation, stocks-only ed ETF-only testati, nessuna variante promossa.
- [x] Benchmark-objective comparison: obiettivi piu' vicini al benchmark testati, nessuna variante promossa.
- [x] Notebook `04_backtest_analysis.ipynb`.
- [x] Soglie scanner e modello versionate.

## Milestone 3 - News + Context

- [x] Primo connettore GDELT macro-news daily laggato.
- [ ] Event classifier: earnings, macro, politica, shock.
- [ ] `news_risk_filter`: block, reduce size, warning.
- [ ] Fallback se news API non risponde.
- [ ] Report su quanti trade vengono bloccati e perche'.
- [ ] Specifica approccio cross-sectional: label ranking relativo, portfolio construction e metriche dedicate.

Vedi [[news-risk-engine]].

## Milestone 3B - Small-Cap Swing Research Track

- [x] Scrivere spec long-only small/mid-cap swing.
- [x] Universe builder small/mid-cap con filtri liquidita', prezzo e dollar volume.
- [x] Data-quality report per small/mid-cap candidate.
- [x] Market-regime guardrail per IWM EMA 50/200, VIX e breadth prima dello scanner.
- [x] Scanner rule-based long-only: panic reversal, breakout continuation, post-gap drift.
- [x] Execution assumptions dedicate: no naive next-open, skip gap apertura >8-10%, spread/slippage conservativi, no fill se liquidita' insufficiente.
- [x] Capacity constraint: size massima come percentuale del dollar volume medio.
- [x] Candidate export giornaliero con diagnostica universe, data-quality, scanner, regime ed execution.
- [x] Benchmark coerenti: IWM, equal-weight universe, random-entry baseline, ticker holding-window benchmark.

Vedi [[small-cap-swing-research-spec]].

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
