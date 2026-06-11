# 2026-05-22 - SEC8K Tape Oracle Intraday Data Contract

## Contesto

`TRIAL-SEC8K-DIRECTION-001` now has a frozen Tape Oracle preregistration, but execution must remain blocked until the intraday data requirements are explicit.

## Cambiamento

Added `SEC8K-TAPE-ORACLE-INTRADAY-DATA-CONTRACT-001` under `experiments/provider_aware_research/sec8k_tape_oracle_intraday_data_contract_gate_20260522/`.

The gate requires:

- existing SEC Item 2.02 event panel;
- BMO/AMC reaction-session mapping;
- 1m or finer RTH bars;
- America/New_York timestamps;
- fixed oracle/entry/flat windows;
- same-symbol first-15m control volume baseline;
- spread/slippage/impact/commission proxies;
- 500 bps round-trip cost model.

## Verifiche

- `py -3 -m pytest tests/test_sec8k_tape_oracle_intraday_data_contract_validator.py -q`
- `py -3 -m src.experiments.sec8k_tape_oracle_intraday_data_contract_validator --contract-dir experiments/provider_aware_research/sec8k_tape_oracle_intraday_data_contract_gate_20260522`

## Risultato

Targeted tests pass `5/5`; validator passes `51/51`.

## Decisione

`SEC8K_TAPE_ORACLE_INTRADAY_DATA_CONTRACT_PASS`. The gate is valid but non-executable. Next safe step: provider-selection and bounded approval for intraday RTH coverage.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
