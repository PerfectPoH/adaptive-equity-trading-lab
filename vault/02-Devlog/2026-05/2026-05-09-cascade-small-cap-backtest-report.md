---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-backtest-report
tags: [devlog, small-cap, backtest, report, diagnostics, tdd]
---

# 2026-05-09 - Small-Cap Backtest Report

## Contesto

Dopo candidate export e benchmark small-cap, serviva un report dedicato che collegasse candidati operativi, benchmark coerenti e diagnostica di filtro. Questo non sostituisce ancora un engine trade-by-trade completo, ma fornisce un primo proxy valutativo riproducibile.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_backtest_report.py`.
- Modulo `src/analysis/small_cap_backtest_report.py`.
- Funzione `build_small_cap_backtest_report`.
- Funzione `write_small_cap_backtest_report_markdown`.

## Input

```text
candidate_export
benchmark_report
primary_benchmark=equal_weight_universe
```

## Output principali

```text
verdict
candidate_summary
primary_benchmark
strategy_proxy_return
primary_benchmark_return
excess_return
benchmark_report
setup_counts
regime_block_reasons
execution_skip_reasons
decision
```

## Verdict

```text
beats_primary_benchmark
underperforming_primary_benchmark
insufficient_data
```

## Logica

- `strategy_proxy_return` usa il benchmark `ticker_holding_window`.
- Il benchmark primario default e' `equal_weight_universe`.
- `excess_return` = `ticker_holding_window - equal_weight_universe`.
- La diagnostica aggrega setup operativi, motivi di blocco regime e motivi di skip execution.

## Nota metodologica

Questo report e' un ponte verso il backtest small-cap dedicato. Non deve essere interpretato come simulazione completa di ordini, fill, overlapping positions o portfolio constraints multi-simbolo.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_backtest_report.py
4 passed
```

## Prossima mossa

Costruire un runner small-cap che produca automaticamente candidate export, benchmark report e markdown report su finestre storiche definite.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-candidate-export]], [[2026-05-09-cascade-small-cap-benchmarks]], [[Roadmap-Master]].
