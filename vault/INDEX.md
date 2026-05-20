---
tipo: index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-20
tags: [vault, index, obsidian, trading-lab]
---

# Indice - Vault Adaptive Equity Trading Lab

> Cervello condiviso del progetto. Questo vault tiene insieme architettura, fasi, memoria AI, errori gia' visti, report e decisioni operative.
>
> Prima di scrivere codice leggere sempre: [[Protocollo-Collaborazione]], [[Memoria-AI]], [[Roadmap-Master]], [[backlog]].
>
> Per capire dove mettere una nota nuova, leggere [[Vault-Structure]].

---

## Quick links

- [[Protocollo-Collaborazione]] - ruoli, workflow, limiti operativi.
- [[Memoria-AI]] - errori da non ripetere e best practice.
- [[Architettura]] - struttura tecnica del sistema.
- [[Roadmap-Master]] - fasi del progetto e gate.
- [[Regole-Quant]] - regole anti-bias, backtest, execution e risk.
- [[Regole-Codice]] - regole pratiche per lavorare nel repo.
- [[Vault-Structure]] - regole per tenere ordinato il vault.
- [[backlog]] - bug, rischi aperti e tech debt.
- [[Report-Milestone1-2026-05-08]] - primo report operativo.
- [[Report-Small-Cap-Research-Status-2026-05-12]] - stato aggiornato track small-cap.
- [[Report-Post-Run-Validation-Gate-2026-05-20]] - gate post-run per coerenza artifact ed execution guardrails.
- [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]] - gate data-ingestion XMOM prima dello sblocco pre-run.
- [[Report-XMOM-Data-Ingestion-Synthetic-Dry-Run-2026-05-20]] - dry run sintetico isolato del data-ingestion gate.
- [[Report-XMOM-Real-Data-Ingestion-2026-05-20]] - ingestione reale Databento XMOM con pre-run gate pronto.
- [[Report-XMOM-Trial-001-Execution-2026-05-20]] - prima esecuzione preregistrata XMOM: primary metric positiva, outlier stress blocca promozione.
- [[Report-XMOM-Trial-001-Forensic-Interpretation-2026-05-20]] - autopsia top winner XMOM: possibile catalyst exposure, non edge validato.
- [[Report-XMOM-Catalyst-Classification-2026-05-20]] - classificazione catalyst su tutti gli 11 trade XMOM; domanda aggiornata a continuation vs fade.
- [[Report-XMOM-Catalyst-Trial-001-Preregistration-Spec-2026-05-20]] - spec-only per trial catalyst-aware continuation vs fade, non eseguito.
- [[Report-XMOM-Catalyst-Preregistration-Validator-2026-05-20]] - validator strutturale della spec catalyst-aware, 58/58 pass.
- [[Report-XMOM-Catalyst-Feature-Rationale-2026-05-20]] - review teorica feature/soglie catalyst-aware, soglie operative ancora TBD/non eseguibili.
- [[small-cap-ranking-exits-research-track]] - track separato ranking/uscite design-only con trial accounting obbligatorio.
- [[Project-Handoff]] - handoff completo per altre chat o agenti.
- [[Devlog-Index]] - cronologia ordinata delle sessioni.
- [[Documentazione-Index]] - report e handoff ordinati.

---

## Struttura

| Cartella | Contenuto |
|---|---|
| `00-Progetto/` | Documenti fondazionali: architettura, roadmap, memoria AI, protocollo, regole, wikilinks |
| `01-Feature/` | Specifiche delle feature e dei moduli da costruire |
| `02-Devlog/YYYY-MM/` | Log cronologico delle sessioni, uno per sessione |
| `03-Bug/` | Backlog bug, rischi, tech debt e limiti noti |
| `03-Bug/_archive/` | Storico bug risolti quando il backlog cresce |
| `04-Documentazione/Reports/` | Report, analisi e postmortem |
| `04-Documentazione/Handoff/` | Handoff completi per altre chat o agenti |
| `04-Documentazione/_archive/` | Documenti superati mantenuti per memoria |

---

## Documenti vivi

### 00-Progetto

- [[Architettura]] - stack e flusso dati.
- [[Roadmap-Master]] - milestone e definition of done.
- [[Memoria-AI]] - memoria operativa anti-errori.
- [[Protocollo-Collaborazione]] - come devono lavorare umano e agenti.
- [[Regole-Codice]] - convenzioni tecniche.
- [[Regole-Quant]] - regole quantitative e anti-bias.
- [[Vault-Structure]] - organizzazione e naming.
- [[Wikilinks]] - mappa dei nodi principali.

### 01-Feature

- [[mvp-core-pipeline]] - specifica della Milestone 1.
- [[news-risk-engine]] - filtro news/eventi, spostato dopo MVP.
- [[graphify-vault-memory]] - uso futuro di Graphify e vault.

### 02-Devlog

- [[Devlog-Index]] - cronologia delle sessioni.

### 03-Bug

- [[backlog]] - bug, rischi aperti, limiti noti.

### 04-Documentazione

- [[Documentazione-Index]] - indice report e handoff.
- [[Report-Milestone1-2026-05-08]] - stato della prima implementazione.
- [[Report-Small-Cap-Research-Status-2026-05-12]] - stato della research track small-cap.
- [[Project-Handoff]] - riepilogo completo trasferibile ad altri agenti.
- [[README]] - note sulla cartella documentazione.

---

## Stato attuale

Milestone 1 e' stata scaffoldata e la pipeline gira end-to-end:

- test: `48 passed`;
- run pipeline default: `20260508_203628`;
- backtest out-of-sample 2024: non batte buy-and-hold;
- fallimento documentato: la baseline e' funzionante ma non ancora competitiva;
- default sperimentale corrente: `use_news=false`, `model_type=random_forest`, universo completo 10 simboli, feature set baseline, isotonic calibration, `model_probability > 0.25`, stop `1.5 ATR`, take-profit `3 ATR`, timeout 10 giorni, nessun daily rank filter, rischio 1% per trade;
- diagnosi principale: 1093 segnali su 10 simboli, rendimento medio 2024 circa 6.49%, ma ancora sotto buy-and-hold;
- split temporale purgato: le ultime barre di train/validation/test vengono rimosse quando la label a 10 giorni supererebbe il confine;
- downloader robusto: se `yfinance` fallisce, usa l'ultimo snapshot locale valido;
- news GDELT macro 2020-2024 collegate come feature laggate sperimentali, non default.
- calibrazione isotonic implementata e promossa a default di ricerca dopo walk-forward;
- feature-regime analysis aggiornata: low rolling volatility, high distance-from-high e low calibrated probability sono bucket fragili.
- regime-filter validation aggiornata: i filtri non migliorano strategy return; combined filters migliorano drawdown ma tagliano troppo rendimento.
- walk-forward validation completata: default aggiornato a isotonic `0.25`; verdict `positive_but_under_benchmark`.
- model comparison completata: Logistic Regression e HistGradientBoosting non battono Random Forest sotto vincolo minimo di 30 trade validation.
- feature-set comparison completata: `enhanced_context` non viene promosso perche' peggiora il test 2024 rispetto al baseline default.
- target/exit comparison completata: backtest ora rispetta timeout e finalizza trade aperti; nessuna variante ATR viene promossa.
- signal-quality/ranking comparison completata: top-N giornaliero testato, ma nessun ranking viene promosso; score e rank restano diagnostici.
- market-exposure comparison completata: 2% risk migliora il 2024 ma non batte buy-and-hold e non viene promosso.
- universe-selection comparison completata: universi ridotti testati, ma nessun subset viene promosso.
- benchmark-objective comparison completata: obiettivi `trade_positive`, `beats_horizon_return` e `tp_and_beats_horizon` testati, ma nessuno batte buy-and-hold out-of-sample.
- model registry append-only aggiunto: ogni run salva `model.joblib`, `model_metadata.json` e una riga in `experiments/model_registry.csv` con hash SHA-256 e configurazione.
- soglie scanner/modello versionate: default tracciato come `thresholds_v2026_05_08_isotonic_025` in summary, experiment log, metadata modello e registry.
- TimeSeriesSplit/walk-forward fold builder completato: i fold annuali sono generati da `build_annual_walk_forward_folds`, mantenendo `wf_2023` e `wf_2024` equivalenti ai fold precedenti.
- hyperparameter comparison completata: Random Forest default/shallow/deeper confrontati con selezione su validation; nessuna configurazione viene promossa perche' resta sotto buy-and-hold.
- priorita' research aggiornate: aggiungere embargo prima di nuove modifiche strutturali; cross-sectional va specificato separatamente; DSR, CPCV, point-in-time data, event-driven e market impact restano gate istituzionali.
- embargo temporale configurabile aggiunto: `embargo_days` disponibile in `temporal_split` e nel builder walk-forward, con default `0` per non alterare la baseline.
- backtest analysis completata: notebook/report riproducibile conferma sottoperformance vs buy-and-hold e identifica peggiori excess return su NVDA, META, TSLA, AMZN e GOOGL.
- pivot strategico proposto: congelare la baseline large-cap ML come controllo negativo e aprire research track long-only small/mid-cap swing, senza short nella prima fase.
- universe builder small/mid-cap aggiunto: `SmallCapUniverseConfig` e `build_small_cap_universe` filtrano market cap, prezzo, volume, dollar volume ed ETF con rejection reasons.
- data-quality report small-cap aggiunto: `SmallCapDataQualityConfig` e `build_small_cap_data_quality_report` segnalano dati mancanti, OHLCV invalidi, zero-volume ed extreme price jumps.
- market-regime guardrail aggiunto: `MarketRegimeGuardrailConfig` e `add_market_regime_guardrail_columns` bloccano segnali/trade quando IWM < EMA 50, VIX > 35 o i dati regime mancano.
- scanner small-cap rule-based aggiunto: `SmallCapSwingScannerConfig` e `add_small_cap_swing_scanner_columns` classificano panic reversal, breakout continuation e post-gap drift senza ML.
- execution planner small-cap aggiunto: `SmallCapExecutionConfig` e `add_small_cap_execution_columns` applicano gap guardrail, spread/slippage, stop/target ATR e capacity cap al 1% del dollar volume.
- candidate export small-cap aggiunto: `SmallCapCandidateExportConfig`, `build_small_cap_candidate_export` e `write_small_cap_candidate_export` producono candidati operativi e diagnostica per rigetti.
- benchmark report small-cap aggiunto: `SmallCapBenchmarkConfig` e `build_small_cap_benchmark_report` calcolano cash, IWM proxy, equal-weight universe, random-entry baseline e ticker holding-window.
- backtest/report proxy small-cap aggiunto: `build_small_cap_backtest_report` e `write_small_cap_backtest_report_markdown` confrontano il proxy holding-window con il benchmark primario e aggregano diagnostica setup/regime/execution.
- historical runner small-cap aggiunto: `SmallCapHistoricalRunConfig` e `run_small_cap_historical_report` producono `candidate_export.csv`, `benchmark_report.csv` e `small_cap_backtest_report.md` per finestre storiche.
- data preparer small-cap aggiunto: `SmallCapPreparedData` e `prepare_small_cap_historical_data` convertono OHLCV + metadata statici in `candidate_metadata`, frame feature-ready, IWM proxy e diagnostica.
- experiment CLI small-cap aggiunta: `run_small_cap_historical_experiment` e `python -m src.experiments.small_cap_experiment_cli` collegano metadata CSV, download OHLCV/IWM/VIX, data preparer e historical runner.
- metadata builder small-cap aggiunto: `build_small_cap_metadata`, `write_small_cap_metadata_csv` e `python -m src.data.small_cap_metadata_builder` generano il CSV `symbol,market_cap,is_etf` da watchlist ticker con diagnostica.
- one-shot experiment small-cap aggiunta: `run_small_cap_watchlist_experiment` e `src.experiments.small_cap_experiment_cli` senza `--metadata-path` generano metadata e report storico partendo da `--symbols`.
- smoke run reali small-cap eseguiti: primo run negativo con watchlist fuori range market cap; secondo run su BBAI/LUNR/OPEN/OUST con 32 candidati operativi e verdict proxy positivo vs equal-weight universe.
- report diagnostics small-cap migliorate: markdown e dict report includono universe rejection reasons, scanner reject reasons, metadata diagnostics end-to-end e operational-only notional.
- execution planner core small-cap aggiunto: `SmallCapExecutionPlanner` e `SmallCapExecutionDecision` pianificano decisioni atomiche con next-open gap reject, capacity cap, cash cap e costi/slippage.
- portfolio backtester core small-cap aggiunto: `run_small_cap_portfolio_backtest` produce trade log, equity curve, summary e rejection summary con cash bloccato/liberato sulle posizioni.
- portfolio report integration small-cap aggiunta: il runner storico scrive `portfolio_trade_log.csv`, `portfolio_equity_curve.csv`, `portfolio_rejections.csv`, `portfolio_summary.csv` e il markdown include sezioni portfolio.
- roadmap critica small-cap aggiornata: prima di sector cap/random delay/survivorship sensitivity servono Outlier P&L Breakdown, Score Profile Report e run manifest con config hash.
- portfolio diagnostics report small-cap aggiunto: `portfolio_outlier_breakdown.csv`, `portfolio_score_profile.csv`, sezioni markdown outlier/score e `small_cap_scanner_score` preservato nel trade log.
- smoke portfolio diagnostics completata: portfolio +74.25% ma `top_3_pnl_contribution_pct=1.0086` e `outlier_concentration_alert=True`; verdetto `NON PROMUOVERE`.
- stress test ex-outlier aggiunto: senza top 3 trade vincenti il portfolio passa a -0.64%, `sign_flip_excluding_top_3=True`.
- run manifest small-cap implementato: `src/experiments/run_manifest.py` produce `run_manifest.json` accanto agli altri artefatti del runner storico, con `run_id` univoco, `config_hash` SHA-256 deterministico sulla `SmallCapHistoricalRunConfig`, `created_at`, `schema_version`, `universe`, periodo, `git_commit` e `host`; il markdown del report include la sezione `## Run Manifest` in testa; suite a 148 passed; RISK-023 passa a mitigato.
- smoke ampia small-cap completata: 30 ticker eleggibili, 40 trade, `portfolio_return=-22.16%`, score profile non monotono; verdetto `NON PROMUOVERE`.
- cash starvation diagnostics aggiunta: `portfolio_cash_starvation.csv` e summary; sulla smoke ampia missed median return -4.75% e missed win rate 38.03%, quindi le rejection cash non giustificano piu' capitale/concurrency.
- setup disentangler passivo aggiunto: summary/score/cash starvation per `small_cap_setup`; breakout_continuation e' l'unico setup positivo nel campione, post_gap_drift e' la zavorra principale, score 100 non monotono.
- feature-level diagnostics per setup aggiunta: `portfolio_setup_feature_profile.csv`; mostra regioni feature opposte dentro lo stesso setup, quindi prossimo passo e' rule ablation passivo.
- breakout-only ablation aggiunta: `allowed_setups=["breakout_continuation"]` produce +37.97%, ma resta outlier-driven (`sign_flip_excluding_top_3=True`); prossimo passo rule ablation feature dentro breakout.
- feature filter ablation aggiunta: `open_to_close_return>=0.084459` su breakout produce +140.77%, 22 trade e resta positivo senza top 3 winner; soglia ancora in-sample.
- open-to-close sensitivity aggiunta: `>=0.08` e `>=0.10`; `>=0.10` e' piu' forte (+177.99%, 15 trade, ex-top3 +74.6k) ma richiede validazione temporale.
- temporal split validation aggiunta: `>=0.10` resta forte in H2 (+71.03%, 7 trade, ex-top3 +14.4k) ma H1 e' troppo scarso; edge time-concentrated.
- multi-year validation aggiunta: `>=0.10` su 2022-2024 produce +135.07%, 43 trade, ex-top3 +44.6k; sopravvive ma resta 2024-driven, prossimo gate regime diagnostics.
- regime diagnostics aggiunta: EMA50 non discrimina, IWM sopra EMA200 separa i trade (+153.3k vs -18.3k), VIX non e' filtro ovvio; prossimo gate regime filter configurabile.
- EMA200 regime gate attivo: `regime_filters` migliora a +169.21% e ex-top3 +67.5k, ma 2022/2023 restano negativi; niente paper trading.
- 2023 false-positive error analysis: pattern whipsaw IWM sopra EMA200, ma nessun nuovo filtro; prossimo step OOS H1 2025 congelato.
- OOS H1 2025 congelato: solo 2 trade, -16.09%, benchmark filtrato sotto random; strategia non validata fuori campione.
- OOS full-year 2025: 15 trade, -15.91%; benchmark filtrato positivo ma portfolio negativo, indicando problema di path/sizing/selezione.
- Portfolio mechanics audit: planner portfolio usa quasi tutto il cash e ignora `risk_fraction`; 18 cash-starved missed trades hanno mediana +4.63%, serve fix sizing TDD.
- Risk-based sizing fix: OOS 2025 migliora a +0.92% senza cash starvation, ma ex-top3 resta negativo; validazione strategia ancora fallita.
- Multi-year risk-sizing rerun: EMA200 2022-2024 passa da +169.21% old sizing a +3.60% risk sizing; sotto benchmark e con sign flip ex-top3, quindi vecchio edge declassato a leverage/path artifact.
- Decisione finale: setup `breakout_continuation + open_to_close_return>=0.10 + IWM>EMA200` archiviato come portfolio strategy non promuovibile; ranking/uscite solo in eventuale track separato con trial accounting.
- Track ranking/uscite: `TRIAL-RANKEX-001` validation fallita per sign flip ex-top3; ranking semplice chiuso/non promosso. Data Quality Audit verdict: `NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE`; Lessons Learned riclassifica il lavoro small-cap 2026-05-09..2026-05-14 come stress test metodologico/infrastrutturale, non evidenza di edge. Scaffolding check negative-control su universo fixed large-cap/ETF completato con `TECHNICAL_PASS`; `TRIAL-NCTRL-001` pre-registrato come property-based negative control ma `NOT RUN / NOT IMPLEMENTATION-COMPLETE`. Prossimo lavoro ammesso: TDD infrastruttura P5/P6/P4/reporting/accounting, non esecuzione.

Conclusione: il progetto ha una base tecnica valida, ma la specifica strategia small-cap breakout EMA200 e' archiviata come non promuovibile per capitale reale.

---

## Routine prima di lavorare

1. Apri [[INDEX]].
2. Leggi [[Protocollo-Collaborazione]].
3. Controlla [[Memoria-AI]] per anti-pattern gia' noti.
4. Controlla [[backlog]].
5. Se tocchi strategia, feature, label, risk o backtest, controlla [[Regole-Quant]].
6. A fine sessione aggiorna un devlog in `02-Devlog/YYYY-MM/`.
7. Se aggiungi documenti nuovi, aggiorna [[Devlog-Index]] o [[Documentazione-Index]].
