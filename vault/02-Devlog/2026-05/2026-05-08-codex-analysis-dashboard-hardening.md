---
tipo: devlog
data: 2026-05-08
agente: codex
topic: analysis-dashboard-hardening
tags: [devlog, analysis, dashboard, backtest]
---

# Sessione Codex - Analysis e dashboard hardening

## Contesto

Dopo la creazione del vault, Barak ha chiesto di continuare con il progetto. La roadmap indicava tre follow-up immediati: rafforzare anti-shift, aggiungere equity curve aggregata e documentare meglio perche' la baseline non batte buy-and-hold.

## Cosa ho fatto

- Aggiunto `src/analysis/error_analyzer.py`.
- Aggiunto export `analysis.csv` e `analysis_summary.json`.
- Aggiunto export `equity_curves.csv`.
- Aggiornata dashboard Streamlit con run analysis, equity curve aggregata e diagnosi per simbolo.
- Rafforzato test `backtesting.py`: un segnale deve entrare al next open.
- Corretto `PrecomputedSignalStrategy` usando ordine `limit` al next-open precomputato per evitare validazione SL/TP contro il close precedente.
- Aggiornato `.gitignore` per ignorare `.obsidian/` nella root repo.

## Risultati

- Test: `9 passed`.
- Run pipeline: `20260508_170918`.
- Segnali 2024: 29.
- Simboli con segnali: 2 su 10.
- Simboli sotto buy-and-hold: 9 su 10.
- Strategia media: circa 0.29%.
- Buy-and-hold medio: circa 48%.

## Problemi incontrati

- L'analizzatore assumeva inizialmente indice temporale ordinato; corretto con filtro booleano su date.
- `backtesting.py` segnala ambiguita' quando SL/TP contingent possono essere colpiti nella stessa candela daily dell'ingresso.

## Verifica

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

## Note per la prossima sessione

- Passare a Milestone 2 leggera: error analysis dei trade e walk-forward validation.
- Non aggiungere News Engine o paper trading finche' la baseline non e' capita meglio.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
