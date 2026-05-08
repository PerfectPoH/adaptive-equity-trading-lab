---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-08
tags: [devlog, target-exit, backtest, timeout]
---

# Devlog - Target/Exit Comparison

## Contesto

Dopo model comparison e feature-set comparison, il collo di bottiglia sembrava meno legato al modello e piu' alla definizione del target/exit.

Durante il controllo e' emersa una discrepanza: il label builder considera il timeout a 10 giorni come fallimento, mentre il backtest lasciava la posizione aperta fino a stop/take-profit o fine finestra.

## Cosa e' cambiato

- `PrecomputedSignalStrategy` ora supporta `timeout_bars`.
- `run_backtest` passa `timeout_bars` alla strategia.
- `Backtest(..., finalize_trades=True)` include i trade ancora aperti a fine finestra nelle metriche.
- `run_walk_forward_validation` supporta `TargetExitConfig`.
- Aggiunto `src.experiments.target_exit_comparison`.
- Dashboard aggiornata con `Latest Target/Exit Comparison`.
- Aggiunti test su chiusura timeout.

## Esperimento

Runner:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.target_exit_comparison
```

Configurazioni:

```text
default_1_5x_stop_3x_tp_10d
fast_1x_stop_2x_tp_5d
balanced_1_5x_stop_2_25x_tp_10d
patient_2x_stop_4x_tp_15d
```

## Risultati

```text
wf_2023:
  selected target/exit: default_1_5x_stop_3x_tp_10d
  selected variant: raw
  selected threshold: 0.45
  test strategy return: ~6.50%

wf_2024:
  selected target/exit: balanced_1_5x_stop_2_25x_tp_10d
  selected variant: isotonic
  selected threshold: 0.35
  test strategy return: ~6.36%

mean test strategy return: ~6.43%
mean excess return: ~-68.30%
folds beating buy-and-hold: 0/2
```

Default run aggiornato:

```text
run_id: 20260508_192713
strategy return 2024: ~6.49%
buy-and-hold 2024: ~48.05%
closed trades: 193
win rate: ~54.4%
```

## Decisione

Non promuovere `balanced_1_5x_stop_2_25x_tp_10d`. Viene scelto dalla validation per il fold 2024, ma il suo test 2024 resta leggermente sotto il default.

Decisione importante: il timeout coerente resta nel backtest, anche se abbassa leggermente il vecchio numero. Meglio una simulazione piu' onesta che una performance piu' carina.

La prossima direzione utile e' signal ranking / selezione universo / scelta dei trade, non altro tuning ATR a griglia.

Vedi [[Memoria-AI]], [[Roadmap-Master]], [[Regole-Quant]].
