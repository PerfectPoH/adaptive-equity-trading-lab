---
tipo: roadmap-master
progetto: adaptive-equity-trading-lab
data: 2026-05-08
ultimo-aggiornamento: 2026-05-12
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
- [x] Backtest/report proxy small-cap dedicato con diagnostica setup, regime ed execution.
- [x] Runner storico small-cap end-to-end con export candidati, benchmark report e markdown report.
- [x] Data preparer small-cap per convertire OHLCV + metadata statici in input compatibili con runner storico.
- [x] Orchestratore/CLI small-cap per metadata CSV, download OHLCV/IWM/VIX, data preparer e historical runner.
- [x] Metadata builder small-cap da watchlist ticker a CSV `symbol,market_cap,is_etf` con diagnostica.
- [x] Modalita' one-shot CLI da watchlist ticker a metadata CSV e historical report.
- [x] Smoke run reali one-shot su watchlist small-cap controllate con diagnostica e report storico.
- [x] Report diagnostics small-cap migliorate: universe rejects, scanner rejects, metadata diagnostics e notional operativo.
- [x] Execution planner core small-cap per decisioni atomiche candidate + next open + cash.
- [x] Portfolio backtester core small-cap con cash ledger, trade log, equity curve e rejection summary.
- [x] Integrazione portfolio nel report storico small-cap con artefatti `portfolio_*.csv`.
- [x] Portfolio diagnostics report: outlier P&L breakdown e concentrazione top-N trade.
- [x] Score profile report: decili di `small_cap_scanner_score`, monotonicita', win rate e P&L per bucket.
- [x] Run manifest small-cap: `run_id`, config hash, timestamp e parametri completi prima di sweep estesi.
- [x] Smoke run reale con confronto `portfolio_return` vs `strategy_proxy_return` vs `equal_weight_universe`: `portfolio_return` +74.25%, ma `outlier_concentration_alert=True`, quindi non promuovere.
- [x] Ex-outlier stress test: senza top 3 winner il portfolio passa da +74.25% a -0.64%, `sign_flip_excluding_top_3=True`.
- [x] Smoke ampia su 30 ticker small-cap eleggibili: 40 trade, `portfolio_return=-22.16%`, score non monotono, verdetto `NON PROMUOVERE`.
- [x] Cash starvation diagnostics: 142 rejection valutabili, missed median return -4.75%, missed win rate 38.03%; non giustifica piu' capitale/concurrency.
- [x] Setup disentangler passivo: `small_cap_setup` propagato nei log e diagnostiche per setup; breakout positivo nel campione, post-gap zavorra, score 100 non monotono.
- [x] Feature diagnostics per setup: `portfolio_setup_feature_profile.csv`; conferma regioni feature buone/pessime dentro ciascun setup e ranking scanner troppo grossolano.
- [x] Breakout-only ablation: `allowed_setups=["breakout_continuation"]`, return +37.97% ma `sign_flip_excluding_top_3=True`; promettente ma non promuovibile.
- [x] Feature filter ablation: `open_to_close_return>=0.084459` su breakout produce +140.77%, 22 trade, `pnl_excluding_top_3=+46.0k`, primo filtro non outlier-only.
- [x] Open-to-close sensitivity: soglie arrotondate `>=0.08` e `>=0.10`; `>=0.10` produce +177.99%, 15 trade, `pnl_excluding_top_3=+74.6k`, benchmark filtrato ticker +12.82% vs random +7.94%.
- [x] Temporal split validation: H2 conferma `open_to_close_return>=0.10` (+71.03%, 7 trade, ex-top3 +14.4k), H1 troppo scarso; edge time-concentrated, serve multi-year/rolling.
- [x] Multi-year validation 2022-2024: `>=0.10` produce +135.07%, 43 trade, ex-top3 +44.6k; sopravvive ma P&L e' 2024-driven e 2023 e' negativo.
- [x] Passive regime diagnostics: `portfolio_regime_profile.csv`; EMA50 non discrimina, IWM sopra EMA200 e' il candidate gate (+153.3k vs -18.3k), VIX non e' filtro ovvio.
- [x] Active EMA200 regime gate: `regime_filters` produce +169.21%, 33 trade, ex-top3 +67.5k; migliora P&L ma resta negativo in 2022/2023, quindi no paper trading.
- [x] 2023 false-positive error analysis: perdenti associati a whipsaw/melt-up IWM sopra EMA200; non creare nuovo filtro, prossimo step OOS H1 2025 congelato.
- [x] OOS H1 2025 congelato: solo 2 trade, -16.09%, ticker holding window -6.77% vs random +5.43%; validation gate non superato.
- [x] OOS full-year 2025: 15 trade, -15.91%; ticker holding window +3.05% e random +3.92%, quindi problema di portfolio path/sizing/selezione; validation gate fallito.
- [x] Portfolio mechanics audit: 18 candidati filtrati saltati per cash con return mediana +4.63%; planner usa quasi tutto il cash e ignora `risk_fraction`, serve fix TDD sizing.
- [x] Risk-based sizing fix: `risk_fraction` applicata nel planner, suite 174 passed; OOS 2025 passa da -15.91% a +0.92% ma ex-top3 e' negativo, quindi strategia ancora non validata.
- [x] Rerun 2022-2024 EMA200 gate con risk-based sizing corretto: vecchio +169.21% crolla a +3.60%, sotto benchmark e con sign flip ex-top3; setup non validato come portfolio strategy.
- [x] Decisione finale small-cap breakout EMA200: setup archiviato come portfolio strategy non promuovibile; eventuale ranking/uscite solo come track separato con trial accounting esplicito.
- [x] Aprire nuovo track ranking/uscite separato come proposta di ricerca design-only, senza riusare il vecchio +169% come prova di edge.
- [x] Implementare trial accounting top-level nel `run_manifest.json`, separato dal `config_hash`; test suite 176 passed.
- [ ] Pre-registrare `TRIAL-RANKEX-001` con finestre, baseline e decision rule prima di qualunque backtest o sweep.

Gate metodologico corrente: run manifest, stress test ex-outlier, smoke ampia, cash starvation diagnostics, setup disentangler passivo, feature diagnostics per setup, breakout-only ablation, feature filter ablation e open-to-close sensitivity e temporal split validation e multi-year validation e passive regime diagnostics sono implementati; non aggiungere sector cap, random delay, survivorship sensitivity o opening regime check prima di ripensare scanner/ranking/triage. La smoke ampia ha prodotto `portfolio_return=-22.16%`, score profile non monotono e missed opportunities mediane negative.

Vedi [[small-cap-swing-research-spec]] e [[small-cap-ranking-exits-research-track]].

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
