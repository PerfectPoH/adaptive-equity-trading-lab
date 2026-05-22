# 2026-05-22 - SEC8K Direction Tape Oracle Preregistration

## Contesto

The SEC 8-K multi-symbol diagnostic identified a high-volume/high-volatility Item 2.02 regime, and the XMOM overlap diagnostic showed that XMOM winners clustered near SEC 8-K windows. The missing component is a point-in-time direction source.

## Cambiamento

Added spec-only `PREREG-SEC8K-DIRECTION-001` / `TRIAL-SEC8K-DIRECTION-001` under `experiments/provider_aware_research/sec8k_direction_tape_oracle_preregistration_20260522/`.

The preregistration freezes a long-only positive oracle:

- first RTH tape window `09:30-09:45 America/New_York`;
- hypothetical entry `09:46`;
- same-day flat by `15:55`;
- first-window volume ratio threshold `3.0`;
- cost model `500` bps;
- DSR threshold `0.95`;
- minimum trade count `30`.

## Verifiche

- `py -3 -m pytest tests/test_sec8k_direction_tape_oracle_preregistration_validator.py -q`
- `py -3 -m src.experiments.sec8k_direction_tape_oracle_preregistration_validator --spec-dir experiments/provider_aware_research/sec8k_direction_tape_oracle_preregistration_20260522`

## Risultato

Targeted tests pass `5/5`; validator passes `51/51`.

## Decisione

`SEC8K_DIRECTION_TAPE_ORACLE_PREREGISTRATION_PASS`. Execution remains blocked. The next safe step is a separate intraday data-contract gate for SEC8K Tape Oracle, not a backtest.
