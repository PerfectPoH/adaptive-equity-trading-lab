---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-universe-builder
tags: [devlog, small-cap, universe-builder, tdd]
---

# 2026-05-09 - Small-Cap Universe Builder

## Contesto

Dopo la spec long-only small/mid-cap swing, il primo codice concreto e' l'universe builder. L'obiettivo e' filtrare candidati prima di scanner, label e backtest.

## Cosa e' stato aggiunto

- Test `tests/test_universe_builder.py`.
- Modulo `src/data/universe_builder.py`.
- Config immutabile `SmallCapUniverseConfig`.
- Funzione `build_small_cap_universe` con diagnostica e motivi di esclusione.

## Filtri iniziali

Default:

```text
min_market_cap: 100M
max_market_cap: 5B
min_price: 2.0
min_avg_volume_20d: 500k
min_avg_dollar_volume_20d: 2M
exclude_etfs: true
```

Il builder non scarica dati e non modifica la pipeline large-cap esistente. Opera su una tabella candidati gia' arricchita con metadata e liquidita'.

## Verification

Test mirato:

```text
python -m pytest tests/test_universe_builder.py
4 passed
```

## Prossima mossa

Creare un data-quality report per candidati small/mid-cap e poi decidere come produrre la tabella candidati da yfinance/Tiingo senza introdurre conclusioni robuste su dati sporchi.

Vedi [[small-cap-swing-research-spec]], [[Roadmap-Master]], [[2026-05-09-cascade-small-cap-pivot]].
