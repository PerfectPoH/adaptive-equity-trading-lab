---
tipo: regole-codice
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [codice, python, test, repo]
---

# Regole Codice

## Ambiente

Usare la venv stabile:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Non usare il comando `python` nudo su questo PC se non e' stato verificato: puo' puntare allo stub Microsoft Store.

## Stile

- Moduli piccoli.
- Funzioni pure quando possibile.
- Nomi espliciti.
- Niente astrazioni premature.
- Commenti solo dove aiutano davvero.
- Evitare notebook come sorgente primaria della logica.

## Struttura

```text
src/data        download e snapshot
src/features    indicatori e pipeline feature
src/scanner     filtri candidati
src/models      label, training, prediction
src/strategy    segnali
src/risk        sizing e vincoli
src/backtest    execution, runner, metriche
dashboard       UI Streamlit
tests           test anti-bias e regressione
```

## File da non committare

- `.venv*`
- `__pycache__`
- `.pytest_cache`
- snapshot CSV pesanti
- output run pesanti
- chiavi API
- token broker
- credenziali

## Test minimi

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
```

Se si cambia logica trading:

```powershell
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Vedi [[Protocollo-Collaborazione]] e [[Memoria-AI]].
