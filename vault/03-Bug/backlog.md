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
- Stato: aperto; elevato a gate prerequisito prima di qualunque nuovo trial small-cap dopo RankEx.

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

### RISK-027 - Breakout-only ancora outlier-driven

- Priorita: P1.
- Sintomo: l'ablazione `allowed_setups=["breakout_continuation"]` produce `return_pct=+37.97%`, ma `top_3_pnl_contribution_pct=152.36%` e `sign_flip_excluding_top_3=True`.
- Impatto: il solo setup breakout e' promettente, ma non e' ancora una strategia robusta; resta dipendente da pochi winner.
- Azione: aggiunto filtro configurabile `allowed_setups` nel portfolio backtester, con rejection `setup_excluded` e manifest tracciato.
- Stato: confermato. Prossimo passo: rule ablation passiva dentro breakout su `open_to_close_return`, `intraday_range_pct` e `relative_volume_20d`; non paper trading.
### RISK-028 - Soglia open_to_close_return ancora in-sample

- Priorita: P1.
- Sintomo: `open_to_close_return>=0.084459` su `breakout_continuation` produce 22 trade, `return_pct=+140.77%`, `pnl_excluding_top_3=+46.0k` e `sign_flip_excluding_top_3=False`.
- Impatto: e' la prima regione feature che resta positiva senza top 3 winner, ma la soglia deriva ancora da bucket in-sample e non va promossa direttamente a live rule.
- Stato: confermato. Prossimo passo: benchmark sul sottoinsieme filtrato e sensitivity con soglie arrotondate (`>=0.08`, `>=0.10`) prima di costruire ranking breakout-specifico.
### RISK-029 - Open-to-close threshold richiede validazione temporale

- Priorita: P1.
- Sintomo: `open_to_close_return>=0.10` su `breakout_continuation` produce 15 trade, `return_pct=+177.99%`, win rate 80%, mediana +11.33%, `pnl_excluding_top_3=+74.6k`, e benchmark filtrato ticker +12.82% vs random +7.94%.
- Impatto: e' la migliore ipotesi primaria, ma il campione e' piccolo e ancora in-sample; rischio elevato di selection bias.
- Stato: confermato. Prossimo passo: validazione temporale/walk-forward su soglie congelate `>=0.08` e `>=0.10`, prima di ranking breakout-specifico o paper trading.
### RISK-030 - Edge open-to-close time-concentrated

- Priorita: P1.
- Sintomo: split H1/H2 su soglie congelate mostra che `open_to_close_return>=0.10` e' forte in H2 (`return_pct=+71.03%`, 7 trade, ex-top3 +14.4k, benchmark filtrato +19.55% vs random +4.17%) ma H1 ha solo 3 trade e non valida robustezza.
- Impatto: la migliore ipotesi resta valida, ma potrebbe essere regime-specific o selection bias; non basta per ranking definitivo o paper trading.
- Stato: confermato. Prossimo passo: dati multi-year o rolling/walk-forward con soglie congelate `>=0.08` e `>=0.10`.
### RISK-031 - Multi-year edge resta 2024-driven

- Priorita: P1.
- Sintomo: run 2022-2024 con `open_to_close_return>=0.10` produce 43 trade, `return_pct=+135.07%`, `pnl_excluding_top_3=+44.6k`, ma annual breakdown: 2022 -0.75k, 2023 -29.7k, 2024 +165.5k.
- Impatto: l'ipotesi sopravvive al multi-year e non e' puro H2-2024, ma il P&L e' dominato da regime favorevole 2024; 2023 mostra falsi breakout.
- Stato: confermato. Prossimo passo: diagnostica regime passiva su IWM/VIX (`iwm_close`, `iwm_ema_50`, `iwm_ema_200`, `vix_close`) prima di qualsiasi ranking o paper trading.
### RISK-032 - Regime filter EMA200 non ancora validato come filtro esecutivo

- Priorita: P1.
- Sintomo: diagnostica passiva su `open_to_close_return>=0.10` multi-year mostra `iwm_above_ema_200=False`: 12 trade, -18.3k, win rate 25%, mediana -5.47%; `True`: 31 trade, +153.3k, win rate 61.29%, mediana +3.38%.
- Impatto: EMA200 e' il primo regime candidate gate convincente, ma non e' ancora stato testato come filtro configurabile con rejection metadata e manifest.
- Stato: confermato. Prossimo passo: TDD per `regime_filters` o `require_iwm_above_ema_200`, poi run 2022-2024 con annual breakdown/ex-top3/benchmark filtrato.
### RISK-033 - EMA200 gate ancora 2024-driven

- Priorita: P1.
- Sintomo: run attiva con `regime_filters=[iwm_close > iwm_ema_200]` migliora a +169.21% e `pnl_excluding_top_3=+67.5k`, ma annual breakdown resta 2022 -4.4k, 2023 -15.5k, 2024 +189.1k.
- Impatto: il gate EMA200 e' utile e tracciato, ma non basta per dichiarare strategia pronta; edge ancora concentrato nel regime 2024.
- Stato: confermato. Prossimo passo: annual outlier diagnostics / DSR trial accounting prima di ranking o paper trading.
### RISK-034 - Whipsaw filter tentante ma non validato

- Priorita: P1.
- Sintomo: error analysis 2023 mostra perdenti dopo rally IWM rapidi sopra EMA200 (`IWM 5d +3.76%`, `20d +8.33%`, distance EMA200 +5.19%), ma il pattern non e' abbastanza robusto per diventare filtro.
- Impatto: creare un filtro anti-melt-up ora sarebbe overfitting macro sul 2023.
- Stato: confermato. Prossimo passo: OOS congelato H1 2025 con le regole gia' scelte, senza Relative Strength e senza nuovi filtri.
### RISK-035 - OOS H1 2025 non valida la strategia

- Priorita: P0.
- Sintomo: run OOS congelata H1 2025 con `breakout_continuation`, `open_to_close_return>=0.10`, `iwm_close>iwm_ema_200` produce solo 2 trade, -16.09%, ticker holding window -6.77% vs random +5.43%.
- Impatto: blocca paper trading e ranking production; il sistema resta ipotesi in-sample/multi-year, non strategia validata.
- Stato: confermato. Prossimo passo: broader OOS / universe robustness / trial accounting DSR prima di nuove feature.
### RISK-036 - Portfolio OOS sottoperforma benchmark filtrato

- Priorita: P0.
- Sintomo: OOS full-year 2025 con regole congelate produce 15 trade e -15.91%, mentre `ticker_holding_window` sul subset filtrato e' +3.05% e random entry +3.92%.
- Impatto: il problema non e' solo il segnale, ma la meccanica portfolio: path, sizing, capitale disponibile e selezione tra candidati concorrenti.
- Stato: confermato. Prossimo passo: portfolio mechanics audit e trial accounting/DSR; non aggiungere filtri in-sample per riparare il 2025.
### BUG-037 - Portfolio planner ignora risk_fraction

- Priorita: P0.
- Sintomo: audit OOS full-year 2025 mostra 15 trade eseguiti e 18 candidati filtrati saltati per `insufficient_funds`; i missed trades hanno mediana +4.63% e win rate 61.11%.
- Root cause: `SmallCapExecutionPlanner.plan_trade` usa `target_notional = min(available_cash, max_liquidity_notional)`, quindi puo' allocare quasi tutto il cash su un singolo trade e non usa `risk_fraction`/stop risk sizing.
- Impatto: portfolio P&L non e' interpretabile come strategia pura; path/sizing/cash starvation distorcono OOS e multi-year.
- Stato: risolto con TDD. `SmallCapExecutionPlanner` usa risk-based sizing capped by liquidity/cash; suite 174 passed.
### RISK-038 - OOS positivo dopo sizing ma outlier-dependent

- Priorita: P0.
- Sintomo: dopo risk-based sizing, OOS full-year 2025 migliora da -15.91% a +0.92% e rimuove `insufficient_funds`, ma `pnl_excluding_top_3=-6.97k` e `sign_flip_excluding_top_3=true`.
- Impatto: il fix infrastrutturale e' valido, ma la strategia resta non validata; il portfolio sottoperforma ancora ticker holding window (+3.05%) e random entry (+3.92%).
- Stato: chiuso come non promozione. Rerun 2022-2024 con sizing corretto produce +3.60%, sotto ticker holding window (+5.42%) e random entry (+4.16%), con sign flip ex-top3.
### RISK-039 - Vecchio multi-year EMA200 era leverage/path artifact

- Priorita: P0.
- Sintomo: il vecchio EMA200 multi-year 2022-2024 mostrava +169.21%, ma dopo sizing risk-based corretto scende a +3.60%.
- Impatto: il setup resta debolmente positivo ma sottoperforma ticker holding window (+5.42%) e random entry (+4.16%) e fallisce ex-top3 (`pnl_excluding_top_3=-5.34k`, sign flip true).
- Stato: chiuso. Setup archiviato come portfolio strategy non promuovibile; ranking/uscite solo come eventuale track separato con trial accounting esplicito.

### RESEARCH-040 - Track separato ranking/uscite small-cap

- Priorita: P2.
- Sintomo: il segnale filtrato contiene valore lordo in alcuni subset, ma il portfolio corretto non batte benchmark e fallisce ex-top3.
- Vincolo: non e' continuazione/promozione del setup archiviato; deve avere trial accounting nuovo, benchmark ticker/random/equal-weight, ex-topN, OOS/universe robustness e nessun paper trading fino a nuova validazione.
- Stato: chiuso/non promosso. `TRIAL-RANKEX-001` batte ticker/random nominalmente ma fallisce ex-top3 (`pnl_excluding_top_3=-6282.54`, sign flip true); decisione strategica: chiudere il ranking semplice. Cross-sectional momentum resta direzione preferita, ma e' bloccata finche' non viene redatto un gate data-quality/methodology.

### RISK-041 - Random baseline trattata come punto singolo

- Priorita: P1.
- Sintomo: `random_entry_baseline` viene confrontato come singolo numero seedato.
- Impatto: una strategia puo' sembrare superiore al random pur essendo dentro la distribuzione attesa di baseline casuali.
- Azione: introdurre bootstrap random baseline con N run, percentili e confronto contro distribuzione.
- Stato: gate prerequisito prima del prossimo trial small-cap.

### RISK-042 - Multiple testing ledger insufficiente

- Priorita: P1.
- Sintomo: sweep, ablation e trial small-cap consumano gradi di liberta' anche se documentati.
- Impatto: un futuro gate superato puo' riflettere accumulo di tentativi, non edge reale.
- Azione: creare ledger per famiglia ipotesi con trial/ablation count e soglia corretta almeno in modo ingenuo.
- Stato: gate prerequisito prima del prossimo trial small-cap.

### RISK-043 - Audit backtester incompleto dopo bug sizing

- Priorita: P1.
- Sintomo: BUG-037 ha mostrato che una singola assunzione del planner cambiava radicalmente i risultati.
- Impatto: cash release timing, slippage, costi, chiusura trade a fine periodo o calendario possono introdurre bias residui.
- Azione: mini-audit documentale/TDD di `SmallCapPortfolioBacktester` prima di nuove interpretazioni strategiche.
- Stato: gate prerequisito prima del prossimo trial small-cap.

### RISK-044 - Universo retro-ricostruito non as-of

- Priorita: P1.
- Sintomo: file universe creati oggi possono essere applicati retroattivamente a date storiche.
- Impatto: survivorship e look-ahead bias, soprattutto su cross-sectional momentum.
- Azione: dichiarare e testare universe construction as-of prima di pre-registrare momentum small-cap.
- Stato: gate prerequisito prima del prossimo trial small-cap.

### RISK-045 - Yfinance daily alone non utilizzabile per nuovi trial small-cap

- Priorita: P0.
- Sintomo: audit pre-registrato su eventi indipendenti mostra `TUP` e `MULN` non scaricabili da `yfinance` nelle finestre critiche; `CNGL` scaricabile ma halt non esplicito e zero-volume elevato.
- Impatto: survivorship/provider availability puo' rimuovere proprio gli eventi distressed/corporate-action-heavy che dominano il rischio small-cap.
- Azione: non aprire nuovi trial small-cap con `yfinance` daily alone come fonte primaria; valutare provider con delisted symbols/corporate actions o universo metodologico piu' affidabile.
- Stato: aperto/bloccante per `TRIAL-XMOM-001`.

### RESEARCH-046 - Negative control scaffolding check su universo fixed large-cap/ETF

- Priorita: P1.
- Sintomo: dopo il data-quality audit, la pipeline deve essere provata su dati piu' affidabili senza aprire un trial strategico.
- Vincolo: modificabili solo parametri universe-scope (`max_market_cap`, `exclude_etfs`, eventuale `min_market_cap`); non modificare soglie scanner, execution, portfolio, regime guardrail.
- Azione: eseguire scaffolding check tecnico su universo fixed large-cap/ETF per verificare che candidate export, manifest, benchmark, backtester e diagnostiche girino senza tuning.
- Stato: completato con `TECHNICAL_PASS`; output `experiments/runs/nctrl_scaffolding_2024_20260515`, `run_id=run_nctrl_scaffolding_20260515`, `config_hash=732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`. Prossimo passo ammesso: preregistrazione `TRIAL-NCTRL-001`, non esecuzione.

### RESEARCH-047 - Implementare infrastruttura property-check per TRIAL-NCTRL-001

- Priorita: P1.
- Sintomo: `TRIAL-NCTRL-001` e' pre-registrato, ma non e' eseguibile finche' non esistono P5/P6/P4/reporting/accounting wiring.
- Azione: implementare con TDD bootstrap random baseline N=1000, random-entry simulator che preserva execution/portfolio/risk_fraction, fixture cash-ledger timing, property-check report writer e trial accounting wiring.
- Stato: completato come infrastruttura TDD; verificati 43 test mirati passati. `TRIAL-NCTRL-001` non eseguito in questo step.

### RESEARCH-048 - Eseguire TRIAL-NCTRL-001 come property-based negative control

- Priorita: P1.
- Sintomo: dopo `RESEARCH-047`, il trial era pronto per una singola esecuzione pre-registrata come property check, non come strategia.
- Azione: eseguire `TRIAL-NCTRL-001`, generare bootstrap baseline, random-entry sign-flip report e property report P1-P8.
- Stato: completato con `PROPERTY_CHECK_PASS`; output `experiments/runs/nctrl_trial_001_2024_20260517`, `run_id=run_nctrl_trial_001_20260517`, `config_hash=732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`. Nessuna promozione strategica.

### RESEARCH-049 - Chiudere programma NCTRL e fissare prossimi binari ammessi

- Priorita: P1.
- Sintomo: dopo il pass di `TRIAL-NCTRL-001`, serviva separare esplicitamente technical pass da strategy promotion.
- Azione: creare decision note finale del programma NCTRL con stato, limiti e prossime direzioni ammesse.
- Stato: completato; programma NCTRL chiuso come `CLOSED / TECHNICAL PASS`. Prossimi lavori ammessi: data/provider evaluation, hardening tooling, o nuova track non-small-cap pre-registrata. Vietati alpha sweep e promozione strategica.

### RESEARCH-050 - Specificare gate valutazione data provider small-cap

- Priorita: P1.
- Sintomo: `yfinance` daily alone e' `NOT_USABLE_FOR_SMALL_CAP_TRIALS`; prima di riaprire small-cap serve un piano provider/dataset, non un nuovo trial.
- Azione: definire requisiti hard/soft per provider su point-in-time universe, delisted symbols, corporate actions, raw/adjusted prices, halt/suspension, riproducibilita' e licensing.
- Stato: completato come spec-only in [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]]. Nessun provider selezionato, nessun backtest autorizzato, nessun trial aperto.

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
