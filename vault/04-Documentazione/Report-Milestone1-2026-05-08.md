---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [milestone1, report, backtest, risultati]
---

# Report Milestone 1 - 2026-05-08

## Obiettivo

Creare la prima pipeline completa del progetto:

```text
download -> snapshot -> feature -> scanner -> label -> model -> signals -> risk -> backtest -> log -> dashboard
```

## Stato

Implementazione MVP completata in prima versione.

## Verifica

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
```

Risultato:

```text
7 passed
```

Pipeline:

```powershell
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Run principale aggiornato:

```text
20260508_170918
```

## Risultati backtest

```text
strategy_return:       circa 0.29%
buy_and_hold_return:   circa 48.0%
excess_return:         circa -47.8%
beats_buy_and_hold:    false
```

## Analisi del run

```text
symbols_analyzed:          10
total_signals:             29
total_executable_signals:  29
total_skipped_signals:     0
symbols_with_signals:      2
symbols_with_trades:       2
underperforming_symbols:   9
outperforming_symbols:     1
```

Findings:

- 9 simboli su 10 sottoperformano buy-and-hold.
- I segnali sono concentrati in 2 simboli su 10.
- NVDA produce la maggior parte dei segnali, ma resta sotto-esposta rispetto al trend enorme del 2024.
- TSLA produce pochi segnali e ritorno negativo.

## Interpretazione

La pipeline funziona, ma la strategia baseline non e' competitiva. Questo e' un risultato utile: i test anti-bias passano, il sistema non nasconde un fallimento, il confronto buy-and-hold e' esplicito e la prossima fase deve lavorare su analisi errori, tuning e validazione.

## Limiti

- Dati `yfinance`, quindi non point-in-time.
- Survivorship bias presente.
- backtesting.py non e' un simulatore execution realistico.
- Alcuni SL/TP su daily OHLC sono ambigui nella stessa candela dell'ingresso.
- Nessun news filter.
- Nessun walk-forward tuning.
- Nessuna calibration.
- Nessuna validazione istituzionale.

## Prossime mosse

1. Analizzare trade vincenti/perdenti.
2. Rafforzare `test_pipeline_no_lookahead.py`.
3. Aggiungere walk-forward validation.
4. Migliorare logging parametri.
5. Solo dopo valutare scanner/model migliorati.

Vedi [[Roadmap-Master]], [[backlog]], [[mvp-core-pipeline]].
