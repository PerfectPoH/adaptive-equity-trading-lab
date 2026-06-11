# Report SEC8K Tape Oracle Intraday Data Contract - 2026-05-22

Decision: `SEC8K_TAPE_ORACLE_INTRADAY_DATA_CONTRACT_PASS`

## Scope

Created `SEC8K-TAPE-ORACLE-INTRADAY-DATA-CONTRACT-001` for `TRIAL-SEC8K-DIRECTION-001`. This gate defines the minimum acceptable intraday data contract for the SEC 8-K Tape Oracle preregistration.

No provider was selected, no provider query was performed, no intraday data was downloaded, no extractor was implemented, no oracle signals were computed, no backtest was executed, and no paper/live trading or strategy promotion occurred.

## Required Contract

- Event source: existing SEC Item 2.02 reaction-session panel only.
- Eligible events: BMO/AMC mapped reaction sessions only.
- Bar frequency: 1 minute or finer RTH bars.
- Session: `09:30-16:00 America/New_York`.
- Oracle window: `09:30-09:45 America/New_York`.
- Hypothetical entry: `09:46 America/New_York`.
- Same-day flat: `15:55 America/New_York`.
- Volume baseline: median first-15m RTH volume on non-event control sessions for the same symbol.
- Volume threshold: `3.0`.
- Required cost model: `500 bps` round-trip minimum.

## Validation

Validator: `src.experiments.sec8k_tape_oracle_intraday_data_contract_validator`

Result: `51/51` checks passed.

Targeted tests: `5/5` passed.

## Decision

The data contract is valid but non-executable. The next safe step is a separate provider-selection and one-call/limited-scope approval gate for intraday RTH data coverage.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
