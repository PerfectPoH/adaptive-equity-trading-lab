---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-setup-feature-diagnostics
tags: [devlog, small-cap, diagnostics, setup-disentangler, feature-diagnostics, scanner]
---

# 2026-05-11 - Small-Cap Setup Feature Diagnostics

## Obiettivo

Proseguire il disentangler passivo aggiungendo diagnostiche feature-level dentro ciascun `small_cap_setup`, senza modificare ranking, sizing, execution o logica di portafoglio.

## Implementazione

Feature scanner ora propagate in `candidate_export.csv`, `portfolio_trade_log.csv` e rejection log:

```text
gap_pct
open_to_close_return
close_position_daily_range
intraday_range_pct
relative_volume_20d
atr_pct
distance_from_20d_high
rolling_volatility_20d
```

Nuova diagnostica:

```text
build_setup_feature_profile_report
```

Nuovo artefatto:

```text
portfolio_setup_feature_profile.csv
```

Nuova sezione markdown:

```text
## Setup Feature Profile Report
```

## Test

Workflow TDD:

```text
RED: test: add setup feature diagnostics coverage
GREEN: feat: add setup feature diagnostics
```

Verifica mirata:

```text
pytest tests/test_small_cap_candidate_export.py tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_portfolio_diagnostics.py tests/test_small_cap_backtest_report.py tests/test_small_cap_historical_runner.py
41 passed
```

Full suite:

```text
pytest
160 passed
```

## Validazione dati

La run storica precedente non conteneva ancora le colonne feature nel `candidate_export.csv`, quindi non era possibile retro-fillare correttamente la feature-profile. E' stata rigenerata una run compatibile:

```text
experiments/runs/small_cap_setup_feature_diag_20260511
metadata: data/small_cap_metadata_eligible_subset30_20260511.csv
periodo: 2024-01-02 -> 2024-12-27
```

Risultati setup summary invariati rispetto al quadro precedente:

```text
breakout_continuation: 16 trade, total_pnl +3,747.06, avg_return +2.93%, median +0.33%, win_rate 50%
panic_reversal:         8 trade, total_pnl -3,148.00, avg_return -0.02%, median +1.37%, win_rate 50%
post_gap_drift:        16 trade, total_pnl -22,760.47, avg_return -1.19%, median +0.76%, win_rate 50%
```

Score profile ancora non monotono:

```text
breakout_continuation Q1 score 83.33: +12,354.33 P&L, avg_return +4.21%
breakout_continuation Q2 score 100:   -8,607.27 P&L, avg_return -6.03%

panic_reversal Q1 score 80:           -1,852.97 P&L, avg_return +1.06%
panic_reversal Q2 score 100:          -1,295.04 P&L, avg_return -3.24%

post_gap_drift Q1 score 80:           -23,378.68 P&L, avg_return -0.50%
post_gap_drift Q2 score 100:          +618.21 P&L, avg_return -3.28%
```

## Evidenze feature-level

### breakout_continuation

`open_to_close_return` distingue meglio dello score aggregato:

```text
Q4: 0.1123 -> 0.1848, 4 trade, +25,846.52 P&L, avg_return +13.38%, win_rate 75%
Q2: 0.0290 -> 0.0842, 4 trade, -12,057.46 P&L, avg_return -5.45%, win_rate 25%
```

`intraday_range_pct` mostra lo stesso pattern non lineare:

```text
Q4: 0.1188 -> 0.1955, 4 trade, +9,156.42 P&L, avg_return +10.62%, win_rate 75%
Q2: 0.0714 -> 0.1003, 4 trade, -12,057.46 P&L, avg_return -5.45%, win_rate 25%
```

`relative_volume_20d` non e' monotona:

```text
Q3: 1.8963 -> 2.1424, 4 trade, +10,405.26 P&L, avg_return +8.95%
Q4: 2.3983 -> 3.3270, 4 trade, +8,131.27 P&L, avg_return +4.69%
Q2: 1.6592 -> 1.7896, 4 trade, -10,881.10 P&L, avg_return -4.04%
```

Interpretazione: breakout_continuation non va scartato, ma il ranking deve guardare intensita' intraday/open-to-close e non solo score booleano.

### post_gap_drift

`gap_pct` individua una zona ad alto rischio:

```text
Q4 gap 4.52% -> 7.85%, 4 trade, -28,363.06 P&L, avg_return -14.55%, win_rate 25%
Q2 gap 0.34% -> 1.05%, 4 trade, +505.34 P&L, avg_return +5.43%, win_rate 75%
Q3 gap 3.38% -> 4.37%, 4 trade, +20,568.17 P&L, avg_return +5.33%, win_rate 50%
```

`intraday_range_pct` conferma una zona estrema negativa:

```text
Q4 range 14.72% -> 27.43%, 4 trade, -28,110.29 P&L, avg_return -13.72%
Q2 range 6.94% -> 9.98%, 4 trade, +33,357.83 P&L, avg_return +16.33%, win_rate 100%
```

`distance_from_20d_high` e' fortemente non lineare:

```text
Q2: -10.22% -> -7.46%, 4 trade, -34,895.95 P&L, avg_return -17.28%
Q3: -4.59% -> -3.61%, 4 trade, +36,474.75 P&L, avg_return +13.57%
Q4: -2.69% -> -1.55%, 4 trade, -30,254.85 P&L, avg_return -8.21%
```

Interpretazione: post_gap_drift non e' semplicemente negativo; ha regioni feature molto diverse. Le soglie attuali mischiano zone buone e pessime.

### panic_reversal

Campione piccolo, ma volatilita' e ATR estreme sono sospette:

```text
atr_pct Q4 16.61% -> 16.68%, 2 trade, -8,397.79 P&L, avg_return -8.53%
rolling_volatility_20d Q4 8.68% -> 10.13%, 2 trade, -8,397.79 P&L, avg_return -8.53%
```

Interpretazione: panic_reversal richiede piu' dati prima di decidere, ma gli estremi di volatilita' non vanno trattati come edge positivo.

## Verdetto

```text
NON PROMUOVERE.
```

La feature-profile rafforza il verdetto: il problema non e' mancanza di capitale, ma ranking/scanner troppo grossolano. Alcune feature separano chiaramente regioni buone e pessime dentro lo stesso setup.

## Prossime azioni

1. Costruire una matrice feature-rule per `breakout_continuation` partendo da `open_to_close_return`, `intraday_range_pct` e `relative_volume_20d`.
2. Per `post_gap_drift`, testare esclusioni passive sulle zone negative: gap alto, intraday range estremo e distance-from-high nelle zone Q2/Q4 osservate.
3. Non cambiare execution finche' non esiste un ranking monotono per setup.
4. Il prossimo passo consigliato e' un `rule ablation report` passivo: simulare filtri feature senza alterare il backtest base.

Vedi [[2026-05-11-cascade-small-cap-setup-disentangler-diagnostics]], [[2026-05-11-cascade-small-cap-cash-starvation-diagnostics]], [[Roadmap-Master]], [[backlog]].
