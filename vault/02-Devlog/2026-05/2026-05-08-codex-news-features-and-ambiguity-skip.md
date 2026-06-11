---
tipo: devlog
data: 2026-05-08
agente: codex
topic: news-features-and-ambiguity-skip
tags: [devlog, news, gdelt, backtest, ambiguity]
---

# Sessione Codex - News features e ambiguity skip

## Contesto

Barak ha chiesto di sistemare i problemi prima di proseguire e, se possibile, collegare gia' le notizie del 2024 per iniziare ad allenare il modello anche con contesto news.

## Cosa ho fatto

- Aggiunto skip conservativo `entry_bar_exit_touch` in label builder ed execution.
- Aggiunta diagnostica del collo di bottiglia scanner/model.
- Aggiunto connettore GDELT DOC API (`src/news/gdelt_doc.py`).
- Aggiunte feature macro-news laggate di un giorno (`src/features/news_features.py`).
- Integrate news features nel training.
- Pulito `experiments/log.csv`, lasciando il run baseline corrente.
- Aggiornati README, docs e vault.

## Risultati

- Test: `13 passed`.
- Run pipeline: `20260508_171849`.
- News cache: `data/news/gdelt_market_news_daily.csv`.
- Segnali 2024: 23.
- Eseguibili: 21.
- Skipped: 2 (`entry_bar_exit_touch`).
- Simboli con segnali: 1 su 10.
- Bottleneck principale: `model_probability_filter` su 9 simboli.
- Strategy return medio: circa 0.38%.
- Buy-and-hold medio: circa 48%.

## Note importanti

- Le news GDELT sono macro-contesto, non company-specific financial news.
- Le news sono laggate di un giorno per ridurre rischio lookahead.
- Serve ablation test con/senza news prima di attribuire valore predittivo alle feature.

## Prossima sessione consigliata

Milestone 2 leggera:

1. calibration report;
2. ablation test con/senza news;
3. tuning soglia `model_probability`;
4. walk-forward validation.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
