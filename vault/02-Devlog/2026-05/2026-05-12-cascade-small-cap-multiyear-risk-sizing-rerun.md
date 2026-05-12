---
tipo: devlog
data: 2026-05-12
agente: cascade
topic: small-cap-multiyear-risk-sizing-rerun
tags: [devlog, small-cap, portfolio, sizing, ema200, multiyear, validation]
---

# 2026-05-12 - Small-Cap Multi-Year Risk-Sizing Rerun

## Obiettivo

Rieseguire il test multi-year 2022-2024 con la stessa ipotesi congelata, ma con il planner corretto a sizing risk-based.

Scopo:

```text
separare edge reale da leverage/path artifact generato dal vecchio sizing quasi all-in
```

## Config congelata

Run nuova:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_risk_sizing_20260512
```

Run precedente comparativa:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_20260511
```

Regole identiche:

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filters = iwm_close > iwm_ema_200
holding_period_bars = 5
max_concurrent_positions = 5
risk_fraction = 0.01
```

Nota metodologica:

```text
risk_fraction non e' stata ottimizzata; e' il valore gia' presente nel manifest e usato nell'OOS corretto.
```

## Confronto vecchio vs nuovo sizing

| Metric | Old cash/liquidity sizing | New risk sizing |
|---|---:|---:|
| Trades | 33 | 41 |
| P&L | 169,213.93 | 3,601.29 |
| Return | 169.21% | 3.60% |
| Ending cash | 269,213.93 | 103,601.29 |
| Insufficient funds | 8 | 0 |
| Total rejections | 467 | 459 |
| Avg notional | 69,520.49 | 9,505.44 |
| Min cash after entry | 0.15 | 63,480.02 |
| P&L ex top1 | 129,171.00 | 447.32 |
| P&L ex top3 | 67,465.86 | -5,339.52 |
| Sign flip ex top3 | false | true |
| Top3 contribution | 0.60x | 2.48x |

## Benchmark invariato

| Benchmark | Return | Observations |
|---|---:|---:|
| ticker_holding_window | 5.42% | 41 |
| random_entry_baseline | 4.16% | 41 |
| equal_weight_universe | 11.93% | 30 |
| iwm_proxy | -11.05% | 1 |

## Annual breakdown nuovo sizing

| Year | Trades | P&L | Win rate | Median return | Avg notional |
|---|---:|---:|---:|---:|---:|
| 2022 | 2 | -963.82 | 50.00% | -2.73% | 8,158.90 |
| 2023 | 13 | -4,119.91 | 38.46% | -1.34% | 10,116.05 |
| 2024 | 26 | 8,685.01 | 53.85% | 4.35% | 9,303.72 |

## Interpretazione

### 1. Il vecchio +169% era largamente artefatto meccanico

Il crollo da:

```text
+169.21% -> +3.60%
```

mostra che la performance precedente era amplificata da sizing quasi all-in, non da un edge portfolio robusto.

La prova principale e':

```text
avg_notional: 69.5k -> 9.5k
min_cash_after_entry: 0.15 -> 63.5k
```

### 2. La cash starvation e' risolta anche multi-year

```text
insufficient_funds: 8 -> 0
trades: 33 -> 41
```

Il motore ora esegue il subset filtrato in modo molto piu' fedele all'ipotesi di segnale.

### 3. Il segnale resta debolmente positivo, ma non batte i benchmark

Nuovo portfolio:

```text
+3.60%
```

Benchmark filtrati:

```text
ticker_holding_window +5.42%
random_entry_baseline +4.16%
equal_weight_universe +11.93%
```

Quindi il portfolio non estrae abbastanza valore dal segnale lordo.

### 4. L'ex-outlier gate fallisce

```text
pnl_excluding_top_3 = -5,339.52
sign_flip_excluding_top_3 = true
```

Questo invalida l'ipotesi come strategia portfolio promuovibile.

## Verdict

```text
Fix sizing confermato.
Vecchio multi-year +169% declassato a leverage/path artifact.
Strategia breakout+open_to_close>=0.10+EMA200 non validata come portfolio strategy.
```

## Decisione operativa

Blocco mantenuto:

```text
no paper trading
no ranking production
no nuovi filtri in-sample
```

Prossima scelta binaria:

1. archiviare questo setup come strategia portfolio;
2. aprire un nuovo track separato su ranking/uscite, con trial accounting esplicito e senza retro-promuovere questi risultati.

## Note dai review comment

I commenti dei colleghi sono incorporati nel verdetto:

- il fix e' infrastrutturale, non tuning;
- il doppio OOS va contato come trial infrastrutturale nel DSR futuro;
- `risk_fraction=0.01` resta congelato;
- il problema residuo non e' piu' cash starvation, ma estrazione inefficiente del valore lordo.

Vedi [[2026-05-12-cascade-small-cap-risk-based-sizing-fix]], [[2026-05-12-cascade-small-cap-portfolio-mechanics-audit]], [[Report-Small-Cap-Research-Status-2026-05-12]], [[Roadmap-Master]], [[backlog]].
