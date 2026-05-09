---
tipo: research-priorities
data: 2026-05-09
progetto: adaptive-equity-trading-lab
tags: [research, roadmap, validation, quant]
---

# Quant Research Priorities - 2026-05-09

## Contesto

Sono stati valutati consigli esterni su come evolvere il progetto dopo i risultati walk-forward e hyperparameter comparison. Il punto centrale e' corretto: la pipeline e' metodologicamente solida, ma l'edge predittivo della baseline non e' ancora dimostrato.

Il rischio da evitare ora e' continuare a cercare performance modificando soglie, risk fraction o iperparametri sullo stesso dataset. Questo aumenterebbe il rischio di overfitting senza risolvere il problema principale: capire se esiste un segnale robusto e validabile.

## Valutazione sintetica dei consigli

### 1. Embargo sui temporal split

Valutazione: priorita' alta e costo basso.

Il progetto ha gia' purging anti-lookahead sulle label forward. Aggiungere un embargo esplicito dopo i confini temporali rende la validazione piu' conservativa contro autocorrelazione, reazioni ritardate e leakage indiretto.

Decisione: aggiungere a Milestone 2 come prossimo hardening della validation.

### 2. Notebook `04_backtest_analysis.ipynb`

Valutazione: priorita' alta.

Prima di cambiare paradigma bisogna sezionare i trade gia' generati: falsi positivi, simboli, regimi, gap, drawdown, holding period, trade skipped e differenza contro buy-and-hold. Questo riduce il rischio di introdurre una nuova architettura senza sapere cosa sta fallendo.

Decisione: resta uno dei prossimi task Milestone 2.

### 3. Approccio cross-sectional

Valutazione: potenzialmente importante, ma strutturale.

Il progetto attuale predice un evento trade-level assoluto (`tp_before_sl`). Un approccio cross-sectional dovrebbe invece stimare ranking relativo tra titoli, poi costruire un portafoglio long-only top-N o long/short market-neutral. Questo puo' ridurre dipendenza dal market beta, ma impatta label, training frame, signal engine, backtest, metriche e benchmark.

Decisione: aggiungere come ricerca Milestone 3/5, non come modifica immediata alla baseline.

### 4. Dati point-in-time e survivorship-bias-free

Valutazione: necessario prima di qualsiasi pretesa robusta o live seria.

I dati `yfinance` sono adatti all'MVP, non a validazione istituzionale. Il problema e' gia' tracciato come RISK-002.

Decisione: confermare in Milestone 6.

### 5. Backtester event-driven e dati intraday

Valutazione: necessario prima del live serio.

Il conservative skip su daily OHLC mitiga RISK-005 ma non risolve l'ordine intraday tra SL e TP. Un motore event-driven con dati intraday e modello di fill/slippage e' necessario per realism upgrade.

Decisione: confermare in Milestone 6.

### 6. DSR, PBO, CPCV

Valutazione: corretti, ma da introdurre dopo aver consolidato gli esperimenti e prima di promuovere qualunque strategia.

Deflated Sharpe Ratio, Probability of Backtest Overfitting e Combinatorial Purged Cross-Validation sono gate anti-data-mining. Non creano edge, ma impediscono di credere a edge falsi.

Decisione: mantenere in Milestone 6; considerare embargo come primo passo compatibile con Milestone 2.

### 7. Fractional differentiation, autoencoder, data augmentation

Valutazione: ricerca avanzata, non priorita' immediata.

Questi strumenti possono essere utili, ma introdurli ora aumenterebbe complessita' senza aver prima chiuso l'analisi diagnostica dei fallimenti correnti.

Decisione: parcheggiare come R&D futura.

### 8. Dynamic market impact

Valutazione: importante per realismo e capacity, non per dimostrare l'edge predittivo della baseline.

Un modello tipo square-root impact o Almgren-Chriss e' utile quando si ragiona su sizing, turnover e capacita'. Per ora il progetto deve prima dimostrare segnale robusto con costi conservativi.

Decisione: confermare in Milestone 6.

## Sequenza consigliata

1. Implementare embargo nei temporal split/walk-forward fold.
2. Creare `04_backtest_analysis.ipynb` per diagnosi trade-level e regime-level.
3. Solo dopo, progettare una mini-specifica per approccio cross-sectional.
4. Rimandare point-in-time data, event-driven backtester, DSR/PBO/CPCV e dynamic impact alla validation gate istituzionale.

## Regola operativa

Non promuovere nuove strategie o default solo perche' migliorano il test 2024. Ogni cambio deve passare validation-only selection, walk-forward, documentazione e decisione esplicita nel vault.

Vedi [[Roadmap-Master]], [[backlog]], [[Regole-Quant]], [[2026-05-08-cascade-hyperparameter-comparison]].
