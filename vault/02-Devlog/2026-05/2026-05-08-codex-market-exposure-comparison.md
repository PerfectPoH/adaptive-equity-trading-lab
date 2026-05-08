---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, market-exposure, risk, walk-forward]
---

# 2026-05-08 - Market Exposure Comparison

## Contesto

Dopo ranking e target/exit, il problema principale rimaneva la sottoesposizione nei bull market: la strategia fa rendimento positivo ma resta lontana dal buy-and-hold.

## Cosa e' cambiato

- Aggiunto `src/risk/market_exposure.py`.
- Aggiunta configurazione `MarketExposureConfig`.
- La pipeline ora salva `risk_fraction`, `risk_fraction_reason`, `market_regime_strong` e `market_exposure_config`.
- `add_execution_columns` puo' usare una `risk_fraction` per riga invece del fisso 1%.
- La walk-forward validation puo' confrontare configurazioni di market exposure.
- Aggiunto runner `src.experiments.market_exposure_comparison`.
- Dashboard aggiornata con il report di market exposure.

## Risultati

Run default aggiornata:

```text
20260508_200621
strategy return 2024: ~6.49%
buy-and-hold 2024: ~48.05%
risk default: 1% per trade
```

Market exposure comparison:

```text
wf_2023:
  selected: default_1pct
  variant: raw threshold 0.45
  test strategy return: ~6.50%

wf_2024:
  selected: fixed_2pct
  variant: isotonic threshold 0.25
  test strategy return: ~11.27%

mean test strategy return: ~8.89%
folds beating buy-and-hold: 0/2
```

## Decisione

Non promuovere `fixed_2pct`.

Motivo: migliora il 2024 soprattutto perche' raddoppia la size, non perche' scopre un edge migliore. Il fold 2023 sceglie ancora il default 1%, e nessuna configurazione batte buy-and-hold out-of-sample.

## Nota Da Ricordare

Aumentare risk fraction e' una leva diagnostica, non una soluzione. Prima di aumentare rischio reale servono edge migliore, drawdown validation, dati migliori e piu' fold.

## Verifiche

```text
pytest: 41 passed
market_exposure_comparison: completato
pipeline default: completata
dashboard localhost:8501: HTTP 200
```
