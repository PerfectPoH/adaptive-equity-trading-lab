---
tipo: bug-tracker
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [bug, backlog, tech-debt, risk]
---

# Backlog Bug, Rischi e Tech Debt

## Bug aperti

Nessun bug critico aperto noto dopo la prima implementazione.

## Rischi aperti

### RISK-001 - Baseline non batte buy-and-hold

- Priorita: P2.
- Sintomo: il primo run 2024 produce circa 0.5% medio contro circa 48% buy-and-hold.
- Causa probabile: filtri e soglie MVP troppo semplici; modello baseline non ancora calibrato; mercato 2024 molto forte per large-cap tech.
- Azione: error analysis in Milestone 2.
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

## Tech debt

### TECH-DEBT-001 - `.venv` parziale da ripulire

- Priorita: P3.
- Sintomo: durante setup Windows ha lasciato una `.venv` parziale.
- Azione: usare `.venv-lab`; eliminare `.venv` quando i lock Windows spariscono.
- Stato: aperto, non bloccante.

### TECH-DEBT-002 - Dashboard minima

- Priorita: P3.
- Sintomo: dashboard utile ma basica.
- Azione: aggiungere equity curve aggregata, grafico drawdown e pannello warning piu' chiaro.
- Stato: aperto.

### TECH-DEBT-003 - Experiment log ancora semplice

- Priorita: P3.
- Sintomo: CSV funziona, ma non traccia ancora tutte le soglie e versioni modello.
- Azione: espandere schema in Milestone 2.
- Stato: aperto.

## Convenzione nuovi bug

Usare ID progressivo `BUG-NNN`; per limiti metodologici usare `RISK-NNN`; per debito tecnico usare `TECH-DEBT-NNN`.

Vedi [[Memoria-AI]] per template completo.
