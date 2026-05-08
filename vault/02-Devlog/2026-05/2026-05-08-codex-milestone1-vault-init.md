---
tipo: devlog
data: 2026-05-08
agente: codex
topic: milestone1-vault-init
tags: [devlog, vault, milestone1]
---

# Sessione Codex - Milestone 1 e vault init

## Contesto

Barak ha chiesto di iniziare la Fase 1 del progetto Adaptive Equity Trading Lab e poi di guardare il vault di `soresina-mercati` per adattarne la struttura a questo progetto.

## Cosa ho fatto

- Creato il repo `adaptive-equity-trading-lab`.
- Implementata una prima pipeline Milestone 1.
- Creato ambiente `.venv-lab`.
- Eseguiti test.
- Eseguita pipeline.
- Creato un vault Obsidian ispirato a Soresina, ma con contenuto specifico trading lab.

## Risultati

- Test: `7 passed`.
- Run pipeline: `20260508_164751`.
- Primo backtest 2024: non batte buy-and-hold.
- Risultato documentato in `experiments/log.csv` e [[Report-Milestone1-2026-05-08]].

## Problemi incontrati

- `python` di sistema puntava allo stub Microsoft Store.
- Una `.venv` parziale e' rimasta bloccata da Windows.
- `yfinance` e' adatto al prototipo ma non alla validazione seria.
- La baseline genera una pipeline valida, non una strategia competitiva.

## Verifica

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

## Note per la prossima sessione

- Leggere [[INDEX]], [[Memoria-AI]], [[backlog]].
- Migliorare analisi errori prima di aggiungere feature avanzate.
- Non passare a paper/live finche' la ricerca non e' piu' solida.
