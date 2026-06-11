---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, universe-selection, walk-forward, validation]
---

# 2026-05-08 - Universe Selection Comparison

## Contesto

Dopo ranking, target/exit e market exposure, il passo successivo era capire se alcuni ticker o sotto-universi fossero responsabili del gap contro buy-and-hold.

## Cosa e' cambiato

- Aggiunta `SymbolSelectionConfig` nella walk-forward validation.
- Aggiunta selezione simboli validation-only: la lista viene scelta nel periodo validation e riusata nel test.
- Aggiunto runner `src.experiments.universe_selection_comparison`.
- Dashboard aggiornata con `universe_selection_comparison_latest.csv`.
- Aggiunto test per evitare che `all_symbols` tagli i simboli con pochi trade.

## Configurazioni Testate

```text
all_symbols
top_7_by_validation_strategy
top_5_by_validation_strategy
top_3_by_validation_strategy
top_5_by_validation_excess
top_5_by_validation_sharpe
positive_validation_strategy
large_cap_stocks_only
index_etfs_only
```

## Risultati

```text
wf_2023:
  selected: large_cap_stocks_only
  symbols: AAPL, AMD, AMZN, GOOGL, META, MSFT, NVDA, TSLA
  variant: raw threshold 0.45
  test strategy return: ~5.59%

wf_2024:
  selected: index_etfs_only
  symbols: QQQ, SPY
  variant: isotonic threshold 0.25
  test strategy return: ~5.48%

mean test strategy return: ~5.54%
folds beating buy-and-hold: 0/2
```

## Decisione

Non promuovere nessun subset.

Motivo: le selezioni cambiano molto tra fold e non battono buy-and-hold. L'ETF-only riduce l'excess negativo nel 2024 ma rinuncia troppo al rendimento assoluto rispetto al default corrente.

## Nota Da Ricordare

Se l'universo viene selezionato guardando il test, diventa data snooping. Qualsiasi blacklist o top-list deve nascere da validation, da dati point-in-time o da regole economiche dichiarate prima.

## Verifiche

```text
pytest: 45 passed
universe_selection_comparison: completato
dashboard localhost:8501: HTTP 200
```


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
