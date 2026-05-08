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
29 passed
```

Pipeline:

```powershell
.\.venv-lab\Scripts\python.exe -m src.pipeline
```

Run principale aggiornato:

```text
20260508_190512
```

## Risultati backtest

```text
strategy_return:       circa 6.99%
buy_and_hold_return:   circa 48.0%
excess_return:         circa -41.1%
beats_buy_and_hold:    false
```

## Analisi del run

```text
symbols_analyzed:          10
total_signals:             1093
total_executable_signals:  1036
total_skipped_signals:     57
symbols_with_signals:      10
symbols_with_trades:       10
closed_trades:             140
trade_win_rate:            circa 52.1%
underperforming_symbols:   9
outperforming_symbols:     1
```

Findings:

- 9 simboli su 10 sottoperformano buy-and-hold.
- Default aggiornato a isotonic calibration con soglia `0.25`.
- 57 segnali sono stati saltati per `entry_bar_exit_touch`, evitando ambiguita' daily OHLC.
- Purged temporal split aggiunto: le label vicine ai confini train/validation/test non usano il futuro del periodo successivo.
- Downloader fallback aggiunto: se `yfinance` fallisce, usa l'ultimo snapshot locale valido.
- GDELT macro-news 2020-2024 e' collegato come feature sperimentale laggata, ma non default.
- News ablation: `mixed_or_inconclusive`; no-news performa meglio nel backtest 2024 corrente.
- Calibration: il modello raw e' overconfident; isotonic migliora Brier/errori e, con soglia 0.25, migliora strategy return.
- Model comparison: Logistic Regression e HistGradientBoosting testati; Random Forest resta default sotto vincolo minimo di 30 trade validation.
- Trade-level: 140 trade chiusi, 73 win, 67 loss; nessun simbolo con media trade negativa.
- Feature-regime: nessun bucket e' netto negativo; regimi piu' fragili legati a low rolling volatility, high distance-from-high e low calibrated probability.
- Regime-filter validation: volume floor, pullback depth, ATR guard e combinato non battono il baseline per rendimento.
- Combined filters migliorano max drawdown, ma riducono troppo strategy return; resta possibile modalita' risk-first futura.

## Interpretazione

La pipeline funziona, ma la strategia baseline non e' competitiva. Questo e' un risultato utile: i test anti-bias passano, il sistema non nasconde un fallimento, il confronto buy-and-hold e' esplicito e la prossima fase deve lavorare su analisi errori, tuning e validazione.

## Limiti

- Dati `yfinance`, quindi non point-in-time.
- Survivorship bias presente.
- backtesting.py non e' un simulatore execution realistico.
- Alcuni SL/TP su daily OHLC sono ambigui nella stessa candela dell'ingresso.
- Primo connettore news presente; ablation corrente non supporta usarlo come default.
- Walk-forward tuning presente, ma solo su due fold.
- Calibration layer default di ricerca, ma ancora non abbastanza validato per live.
- Feature-regime analysis presente, ma ancora su campione piccolo di 140 trade.
- Regime filters testati sullo stesso anno 2024; serve walk-forward prima di promuovere qualunque filtro.
- Nessuna validazione istituzionale.

## Prossime mosse

1. Aggiungere piu' fold walk-forward quando ci sono piu' anni/dati migliori.
2. Migliorare feature/model oltre la soglia.
3. Valutare combined filters solo come modalita' risk-first dopo walk-forward.
4. Migliorare logging parametri e model registry.
5. Solo dopo valutare paper trading.

Vedi [[Roadmap-Master]], [[backlog]], [[mvp-core-pipeline]].
