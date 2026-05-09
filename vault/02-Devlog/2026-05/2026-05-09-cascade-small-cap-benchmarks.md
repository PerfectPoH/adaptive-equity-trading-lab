---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-benchmarks
tags: [devlog, small-cap, benchmarks, analysis, tdd]
---

# 2026-05-09 - Small-Cap Benchmark Report

## Contesto

La spec small-cap richiede benchmark coerenti con universo e setup small/mid-cap. Confrontare soltanto contro SPY o contro buy-and-hold large-cap non e' sufficiente.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_benchmarks.py`.
- Modulo `src/analysis/small_cap_benchmarks.py`.
- Config `SmallCapBenchmarkConfig`.
- Funzione `build_small_cap_benchmark_report`.

## Benchmark supportati

```text
cash_flat
iwm_proxy
equal_weight_universe
random_entry_baseline
ticker_holding_window
```

## Output report

```text
benchmark
return
observations
description
```

## Logica iniziale

- `cash_flat`: rendimento zero sui giorni candidati.
- `iwm_proxy`: rendimento close-to-close su IWM/proxy nel periodo candidato.
- `equal_weight_universe`: media dei ritorni close-to-close dei frame disponibili.
- `random_entry_baseline`: baseline random seeded su date candidate e simboli universo.
- `ticker_holding_window`: media ritorni holding-window dei soli candidati operativi.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_benchmarks.py
4 passed
```

## Prossima mossa

Collegare candidate export e benchmark in un backtest/report small-cap dedicato, mantenendo separata la baseline large-cap congelata.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-candidate-export]], [[Roadmap-Master]].
