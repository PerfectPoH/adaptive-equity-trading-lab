---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: parziale
ultimo-aggiornamento: 2026-05-08
tags: [news, risk, events, roadmap]
---

# Feature - News Risk Engine

## Stato attuale

Implementato un primo connettore **GDELT macro-news daily** per il periodo 2020-2024.

Questa non e' ancora la versione completa del News Risk Engine:

- non classifica earnings;
- non classifica politica/eventi straordinari;
- non blocca trade;
- non usa news specifiche per ogni ticker.

Pero' aggiunge prime feature macro-news laggate al modello.

## Risultato ablation

Ultimo verdict:

```text
mixed_or_inconclusive
```

Le news migliorano la validation ROC AUC ma peggiorano leggermente il return 2024 e il test ROC AUC. Decisione corrente: news disponibili per ricerca, non attive nel default baseline.

## Obiettivo

Aggiungere un filtro news/eventi che protegge il sistema da contesti anomali. Non deve essere un generatore autonomo di segnali buy/sell nella prima versione.

## Uso previsto

Il motore news puo' bloccare trade con rischio evento alto, ridurre size, aggiungere warning al segnale, evitare earnings/macro shock/eventi politici rilevanti e loggare la motivazione.

## Fonti future

- Alpaca News API;
- GDELT;
- Polygon o Finnhub opzionali;
- calendario earnings.

## Output atteso

```json
{
  "symbol": "NVDA",
  "news_risk": "high",
  "action": "block",
  "reason": "Earnings within 24h and negative event cluster"
}
```

## Regole

- Se news API non risponde, comportamento esplicito: block o warning, mai silenzio.
- Non usare news future in backtest.
- Ogni filtro news deve essere misurato.

## Stato futuro

La parte risk-filter resta fuori dalla Milestone 1. Prima servono ablation test con/senza news, calibrazione modello e analisi errori.

Vedi [[Roadmap-Master]] e [[Regole-Quant]].
