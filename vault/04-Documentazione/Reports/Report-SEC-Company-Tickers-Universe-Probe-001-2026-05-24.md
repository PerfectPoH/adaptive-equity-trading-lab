# Report SEC Company Tickers Universe Probe 001 - 2026-05-24

Decision: `SEC_COMPANY_TICKERS_UNIVERSE_SOURCE_BLOCKED_METADATA_INSUFFICIENT`

## Scope

Single official SEC company_tickers.json call. Only derived sample and metadata assessment retained. No market-data download, backtest, parameter sweep, paper/live trading, or promotion occurred.

## Result

- Records observed: 10371
- Observed fields: cik_str, ticker, title
- Has ticker: True
- Has CIK: True
- Has exchange metadata: False
- Has security type metadata: False
- Has active windows: False
- Has delisted symbols: False
- Blockers: missing_exchange_metadata, missing_security_type_metadata, missing_point_in_time_membership, missing_delisted_symbols

## Interpretation

SEC company_tickers.json can support ticker-to-CIK joins, but it is not a sufficient universe source for rare-event alpha research if it lacks point-in-time membership, delisted symbols, exchange and security-type metadata.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
