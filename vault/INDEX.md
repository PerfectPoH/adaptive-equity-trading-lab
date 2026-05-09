---
tipo: index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
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

Conclusione: il progetto ha una base tecnica valida, ma i risultati non vanno interpretati come strategia pronta per capitale reale.

---

## Routine prima di lavorare

1. Apri [[INDEX]].
2. Leggi [[Protocollo-Collaborazione]].
3. Controlla [[Memoria-AI]] per anti-pattern gia' noti.
4. Controlla [[backlog]].
5. Se tocchi strategia, feature, label, risk o backtest, controlla [[Regole-Quant]].
6. A fine sessione aggiorna un devlog in `02-Devlog/YYYY-MM/`.
7. Se aggiungi documenti nuovi, aggiorna [[Devlog-Index]] o [[Documentazione-Index]].
