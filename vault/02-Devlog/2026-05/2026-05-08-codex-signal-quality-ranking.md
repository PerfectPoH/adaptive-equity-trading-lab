---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, signal-quality, ranking, walk-forward]
---

# 2026-05-08 - Signal Quality Ranking

## Contesto

Dopo il confronto target/exit, il passo successivo era migliorare la qualita' dei segnali ed evitare di prendere troppi trade correlati nello stesso giorno.

## Cosa e' cambiato

- Aggiunto `signal_quality_score` nel signal engine.
- Aggiunto filtro opzionale top-N giornaliero con `signal_before_rank`, `signal_rank`, `signal_rank_selected` e `signal_filter_reason`.
- Il ranking puo' usare `signal_quality_score`, `model_probability` o `scanner_score`.
- La pipeline e la walk-forward validation supportano configurazioni di signal quality/ranking.
- Aggiunto runner `src.experiments.signal_quality_comparison`.
- Dashboard aggiornata con il report `signal_quality_comparison_latest.csv`.
- Feature-regime analysis ora include `signal_signal_quality_score`.

## Risultati

Run default aggiornata:

```text
20260508_194750
strategy return 2024: ~6.49%
buy-and-hold 2024: ~48.05%
trade chiusi: 193
trade win rate: ~54.4%
```

Signal quality comparison:

```text
wf_2023:
  selected: top_2_daily_scanner_score
  variant: raw threshold 0.45
  test strategy return: ~3.36%

wf_2024:
  selected: no_quality_rank_filter
  variant: isotonic threshold 0.25
  test strategy return: ~6.49%

mean test strategy return: ~4.93%
folds beating buy-and-hold: 0/2
```

## Decisione

Nessun filtro ranking giornaliero viene promosso.

Motivo: il ranking aiuta nella validation 2022 tagliando esposizione, ma non regge bene nel test 2023. Nel fold 2024 vince ancora il default senza ranking.

## Nota Da Ricordare

`signal_quality_score` non e' una probabilita' e non e' ancora un edge affidabile. Nella run corrente i trade perdenti hanno uno score leggermente piu' alto dei vincenti, quindi lo score resta diagnostico fino a nuova validazione.

## Verifiche

```text
pytest: 37 passed
signal_quality_comparison: completato
pipeline default: completata
dashboard localhost:8501: HTTP 200
```


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
