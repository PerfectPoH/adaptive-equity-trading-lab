# SEC8K Tape Oracle Intraday Data Contract Gate

Status: `SPEC_ONLY_NOT_QUERIED`

Gate: `SEC8K-TAPE-ORACLE-INTRADAY-DATA-CONTRACT-001`

Trial: `TRIAL-SEC8K-DIRECTION-001`

This gate defines the minimum acceptable intraday data contract for testing the SEC 8-K Tape Oracle preregistration. It does not select a provider, query a provider, download data, implement an extractor, compute oracle signals, run a backtest, or authorize paper/live trading.

The purpose is to prevent a repeat of the daily-gap illusion: the future Tape Oracle may only be tested on RTH-native intraday bars with explicit timezone, session, halt, spread/cost, and fixed-window policies.
