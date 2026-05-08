---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: futuro
ultimo-aggiornamento: 2026-05-08
tags: [news, risk, events, roadmap]
---

# Feature - News Risk Engine

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

## Stato

Fuori dalla Milestone 1. Prima servono pipeline, test e analisi errori.

Vedi [[Roadmap-Master]] e [[Regole-Quant]].
