---
tipo: bug-tracker
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-11
tags: [bug, backlog, tech-debt, risk]
---

# Backlog Bug, Rischi e Tech Debt

## Bug aperti

Nessun bug critico aperto noto dopo la prima implementazione.

## Rischi aperti

### RISK-001 - Baseline non batte buy-and-hold

- Priorita: P2.
- Sintomo: il run default `20260508_203628` produce circa 6.49% medio contro circa 48% buy-and-hold.
- Dettaglio: 1093 segnali totali, 1036 eseguibili, su 10 simboli; 9 simboli sotto benchmark.
- Causa probabile: edge ancora debole, target/feature baseline troppo semplici, mercato 2024 molto forte per large-cap tech.
- Azione: feature/model upgrade e validazione su piu' fold in Milestone 2.
- Stato: aperto, documentato.

### RISK-002 - yfinance fragile e non point-in-time

- Priorita: P2.
- Sintomo: provider gratuito, possibilita' di dati mancanti o rettificati.
- Impatto: risultati non adatti a capitale reale.
- Azione: validazioni downloader, snapshot hash, futuro provider point-in-time.
- Stato: limite noto.

### RISK-003 - backtesting.py non simula execution istituzionale

- Priorita: P2.
- Sintomo: framework sufficiente per MVP, non per live realism.
- Impatto: fill, slippage, partial fills e latency non realistici.
- Azione: event-driven backtester in Milestone 6.
- Stato: limite noto.

### RISK-004 - Gap overnight

- Priorita: P2.
- Sintomo: entry al next open corretta, ma gap grossi possono rendere invalida la size stimata.
- Azione: mantenere `max_gap_threshold`, loggare skip e analizzare.
- Stato: parzialmente mitigato.

### RISK-005 - Ambiguita' daily OHLC su SL/TP nella stessa candela

- Priorita: P2.
- Sintomo: `backtesting.py` segnala che alcuni contingent SL/TP possono essere colpiti nella stessa barra daily dell'ingresso.
- Impatto: con dati daily non conosciamo l'ordine intraday degli eventi; alcune metriche possono essere ottimistiche o pessimistiche.
- Azione: skip conservativo `entry_bar_exit_touch` aggiunto; in Milestone 6 passare a event-driven/intraday data prima del live serio.
- Stato: mitigato nel MVP, limite ancora noto.

### RISK-006 - News GDELT non sono news finanziarie point-in-time

- Priorita: P2.
- Sintomo: GDELT macro-news daily aggregate e' utile come contesto, ma non sostituisce feed finanziari, earnings calendars o company-specific news.
- Impatto: il modello puo' imparare correlazioni macro rumorose o non causali.
- Azione: ablation eseguita; tenerle come feature sperimentali laggate, non default.
- Stato: aperto; verdict `mixed_or_inconclusive`.

### RISK-007 - Probabilita' modello non calibrate

- Priorita: P1.
- Sintomo: il modello raw resta overconfident; isotonic calibration migliora le metriche ma e' ancora validata su pochi fold.
- Impatto: usare `model_probability` come probabilita' reale puo' portare a size/risk decision sbagliate.
- Azione: mantenere isotonic 0.25 come default di ricerca, ma validare su piu' fold/dati prima del live.
- Stato: mitigato, non chiuso.

### RISK-008 - Simboli con media trade negativa possono cambiare tra run

- Priorita: P3.
- Sintomo: nel run `20260508_174122`, AMD era negativo; nel run default `20260508_203628` nessun simbolo ha media trade negativa.
- Impatto: blacklist per singolo ticker rischia di essere overfit sul run.
- Azione: niente blacklist finche' il pattern non si ripete su piu' fold o dati migliori.
- Stato: mitigato.

### RISK-009 - Signal quality score non ancora affidabile

- Priorita: P2.
- Sintomo: `signal_quality_score` e ranking top-N non migliorano il walk-forward; nella run corrente i trade perdenti hanno score leggermente piu' alto dei vincenti.
- Impatto: usare lo score come filtro live o sizing input rischia di introdurre overfit e tagliare esposizione utile.
- Azione: mantenerlo diagnostico; riprogettare ranking solo con validazione out-of-sample e piu' anni.
- Stato: aperto, nessun ranking promosso.

### RISK-010 - Aumentare risk fraction non crea edge

- Priorita: P2.
- Sintomo: `fixed_2pct` migliora il fold 2024 fino a circa 11.27%, ma non batte buy-and-hold e aumenta l'esposizione.
- Impatto: confondere aumento size con miglioramento strategico puo' portare a rischio reale eccessivo.
- Azione: mantenere default 1%; usare exposure comparison solo come diagnosi di sottoesposizione.
- Stato: aperto, nessun aumento rischio promosso.

### RISK-011 - Universe selection instabile tra fold

- Priorita: P2.
- Sintomo: `large_cap_stocks_only` viene scelto nel fold 2023, mentre `index_etfs_only` viene scelto nel fold 2024.
- Impatto: scegliere ticker dal validation year rischia di inseguire il regime precedente senza creare edge robusto.
- Azione: mantenere universo completo; riprovare solo con piu' anni, dati migliori o criteri fondamentali/settoriali point-in-time.
- Stato: aperto, nessun subset promosso.

### RISK-012 - Obiettivi benchmark-aware instabili

- Priorita: P2.
- Sintomo: `trade_positive` viene scelto nel fold 2023 perche' batte un benchmark 2022 molto negativo, ma poi nel test 2023 resta circa -98.35% sotto buy-and-hold.
- Impatto: cambiare target ML puo' inseguire il regime di validation invece di creare edge robusto.
- Azione: mantenere `tp_before_sl` come target default; riprovare obiettivi benchmark-aware solo con piu' fold, dati migliori e metrica di rischio piu' severa.
- Stato: aperto, nessun objective alternativo promosso.

### RISK-013 - Validation senza embargo esplicito

- Priorita: P2.
- Sintomo: gli split temporali hanno purging sulle label forward, ma non ancora un embargo esplicito dopo i confini temporali.
- Impatto: feature autocorrelate o reazioni ritardate del mercato possono ridurre la separazione effettiva tra periodi.
- Azione: aggiungere embargo configurabile ai temporal split/walk-forward fold in Milestone 2.
- Stato: mitigato; `embargo_days` disponibile con default `0`.

### RISK-014 - Sweep incrementali su baseline possono diventare data-mining

- Priorita: P2.
- Sintomo: threshold, model comparison, feature set, target/exit, signal ranking, market exposure, universe selection, benchmark objective e hyperparameter comparison sono gia' stati testati.
- Impatto: continuare a ruotare configurazioni sulla stessa baseline aumenta il rischio di overfitting senza creare edge predittivo.
- Azione: fermare sweep non motivati; prima completare notebook diagnostico, embargo e specifica cross-sectional.
- Stato: aperto.

### RISK-015 - Small-cap backtest puo' mentire su spread, slippage e fill

- Priorita: P1.
- Sintomo: small/mid-cap possono avere spread larghi, book sottile e gap premarket/after-hours estremi.
- Impatto: una strategia apparentemente profittevole puo' sparire dopo costi reali o mancati fill.
- Azione: nuova research track solo long-only, con spread/slippage conservativi, no market-order assumption ingenua e filtri liquidita'.
- Stato: aperto.

### RISK-016 - Dilution/offering risk su small-cap

- Priorita: P1.
- Sintomo: molte small/micro-cap emettono azioni, ATM o warrant quando il prezzo spicca.
- Impatto: breakout tecnici possono fallire per pressione di nuova offerta non visibile nei dati OHLCV gratuiti.
- Azione: aggiungere proxy tipo float rotation e data-quality/corporate-action warning prima di promuovere setup small-cap.
- Stato: aperto.

### RISK-017 - Capacity constraint su strategie small-cap

- Priorita: P1.
- Sintomo: strategie su titoli piccoli possono saturare con capitali retail relativamente bassi.
- Impatto: il backtest sovrastima ritorni se assume size non realistiche rispetto al dollar volume.
- Azione: introdurre limite di posizione, ad esempio `position_notional <= 1%` del dollar volume medio a 5 giorni.
- Stato: mitigato nel core; `SmallCapExecutionPlanner` e `SmallCapPortfolioBacktester` applicano capacity/cash cap, ma resta da validare su smoke reali.

### RISK-018 - Regime di mercato small-cap non modellato

- Priorita: P1.
- Sintomo: panic reversal e breakout small-cap cambiano comportamento in bull, bear e stress regime.
- Impatto: un backtest 2020-2024 puo' mescolare regimi incompatibili e nascondere drawdown strutturali.
- Azione: aggiungere guardrail operativi: se IWM < EMA 50 lo scanner non genera segnali, se VIX > 35 tutti i trade sono bloccati, se dati regime mancanti no-trade.
- Stato: parzialmente mitigato; guardrail IWM/VIX implementato sui dati disponibili, ma opening regime check resta futuro.

### RISK-019 - Survivorship bias estremo su small-cap

- Priorita: P1.
- Sintomo: yfinance tende a mostrare sopravvissuti; delisting, fallimenti e reverse split sono frequenti nelle small-cap.
- Impatto: panic reversal su aziende destinate a fallire possono apparire come opportunita' nel backtest.
- Azione: data-quality report deve flaggare delisting risk, reverse split, storico incompleto e limiti del provider.
- Stato: aperto.

### RISK-020 - Float e short-interest non affidabili o ritardati

- Priorita: P2.
- Sintomo: float non affidabile su yfinance; short interest FINRA e' ritardato e non simula disponibilita' reale.
- Impatto: setup squeeze possono essere validati su dati non disponibili o non accurati in tempo reale.
- Azione: fase iniziale long-only senza short-interest; usare float rotation solo come proxy e dichiarare data limits.
- Stato: aperto.

### RISK-021 - Scanner score non monotono

- Priorita: P1.
- Sintomo: il portfolio backtester usa `small_cap_scanner_score` per ordinare i candidati giornalieri, ma non e' ancora dimostrato che score piu' alti producano performance migliori.
- Impatto: il triage puo' allocare capitale ai trade peggiori pur sembrando disciplinato.
- Azione: implementare Score Profile Report per decili di score, con trade count, win rate, P&L, return medio/mediano e monotonicity check.
- Stato: confermato dalla smoke ampia; `portfolio_score_profile.csv` mostra bucket score 100 negativo e peggiore del bucket intermedio, quindi lo score non e' monotono e non va usato per sizing/ranking live.

### RISK-022 - Outlier risk sui rendimenti small-cap

- Priorita: P1.
- Sintomo: pochi trade esplosivi possono generare la maggior parte del P&L.
- Impatto: una equity curve positiva puo' rappresentare una lotteria storica, non un edge replicabile. In live basta perdere uno degli outlier per ribaltare il risultato.
- Azione: implementare Outlier P&L Breakdown con contributo top 1/3/5/10 trade, max single-trade contribution e alert se top 3 trade superano il 40% del P&L totale.
- Stato: confermato dalla smoke e dallo stress ex-outlier; `top_3_pnl_contribution_pct=1.0086`, `outlier_concentration_alert=True` e `sign_flip_excluding_top_3=True`, quindi setup non promuovibile.

### RISK-023 - Overfitting manuale nei run small-cap

- Priorita: P1.
- Sintomo: con scanner rule-based e molte soglie, anche modifiche manuali apparentemente ragionevoli possono diventare sweep non tracciati.
- Impatto: impossibile calcolare in futuro Deflated Sharpe Ratio o Probability of Backtest Overfitting se i tentativi non sono registrati.
- Azione: aggiungere run manifest small-cap con `run_id`, config hash, timestamp, date range, simboli e parametri completi.
- Stato: mitigato. `src/experiments/run_manifest.py` produce `run_manifest.json` accanto agli altri artefatti del runner storico small-cap, con `run_id` univoco, `config_hash` SHA-256 deterministico sulla `SmallCapHistoricalRunConfig`, `created_at`, `schema_version`, `universe`, periodo, `git_commit` e `host`. Il markdown del report ora include la sezione `## Run Manifest` in testa. Verifica: 13 test isolati e 3 di integrazione nel runner (148 passed totali). Resta da estendere il manifest agli altri runner non small-cap se entreranno in sweep tracciati.

### RISK-024 - Cash starvation fraintesa come edge perso

- Priorita: P1.
- Sintomo: molte rejection `insufficient_funds` possono sembrare opportunita' perse e spingere ad aumentare capitale/concurrency senza prova.
- Impatto: si rischia di scalare un ranking non monotono e aumentare drawdown invece di recuperare edge.
- Azione: aggiungere `portfolio_cash_starvation.csv` e summary con return ipotetico dei trade rifiutati per cash.
- Stato: mitigato nel tooling; sulla smoke ampia 142/142 rejection valutabili hanno `median_missed_return_pct=-4.75%` e `missed_win_rate=38.03%`, quindi non giustificano piu' capitale/concurrency.

### RISK-025 - Setup aggregation prematura nello score small-cap

- Priorita: P1.
- Sintomo: `small_cap_scanner_score` aggrega setup diversi e score 100 non e' monotono neanche dentro i setup principali.
- Impatto: il triage seleziona male candidati e puo' amplificare setup strutturalmente negativi.
- Azione: aggiunta diagnostica passiva per `small_cap_setup`: summary, score profile e cash starvation per setup.
- Stato: confermato. Wide smoke: `breakout_continuation` +3.7k P&L, `post_gap_drift` -22.8k P&L, `panic_reversal` -3.1k P&L; score 100 peggiora rispetto ai bucket inferiori nei setup principali. Prossimo passo: feature-level diagnostics per setup, non paper trading.

### RISK-026 - Soglie feature mischiano regioni opposte dentro lo stesso setup

- Priorita: P1.
- Sintomo: la feature-profile per setup mostra bucket feature con performance opposte all'interno dello stesso `small_cap_setup`.
- Impatto: lo score booleano aggregato promuove trade da regioni feature pessime insieme a trade promettenti, impedendo monotonicita' del ranking.
- Azione: aggiunta `portfolio_setup_feature_profile.csv` e sezione report `Setup Feature Profile Report`.
- Stato: confermato. Esempi: `breakout_continuation/open_to_close_return` Q4 +25.8k P&L vs Q2 -12.1k; `post_gap_drift/gap_pct` Q4 -28.4k vs Q3 +20.6k; `post_gap_drift/intraday_range_pct` Q4 -28.1k vs Q2 +33.4k. Prossimo passo: rule ablation passiva per filtri feature, non paper trading.

## Tech debt

### TECH-DEBT-001 - `.venv` parziale da ripulire

- Priorita: P3.
- Sintomo: durante setup Windows ha lasciato una `.venv` parziale.
- Azione: usare `.venv-lab`; eliminare `.venv` quando i lock Windows spariscono.
- Stato: aperto, non bloccante.

### TECH-DEBT-002 - Dashboard minima

- Priorita: P3.
- Sintomo: dashboard utile ma ancora semplice.
- Azione: equity curve aggregata e diagnosi per simbolo aggiunte; resta da migliorare drawdown e warning UX.
- Stato: parzialmente risolto.

### TECH-DEBT-003 - Experiment log ancora semplice

- Priorita: P3.
- Sintomo: CSV funziona, ma non traccia ancora tutte le soglie e versioni modello.
- Azione: espandere schema in Milestone 2.
- Stato: aperto.

## Convenzione nuovi bug

Usare ID progressivo `BUG-NNN`; per limiti metodologici usare `RISK-NNN`; per debito tecnico usare `TECH-DEBT-NNN`.

Vedi [[Memoria-AI]] per template completo.
