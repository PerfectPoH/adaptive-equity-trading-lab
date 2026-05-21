# Gap-down reversion intraday data-contract gate

Status: `SPEC_ONLY_NOT_QUERIED`

Gate id: `GAPREV-INTRADAY-DATA-CONTRACT-001`

Trial id: `TRIAL-GAPREV-001`

This artifact defines the minimum data contract required before any future gap-down reversion extractor, provider query, data download or backtest.

It does not authorize execution.

## Purpose

`TRIAL-GAPREV-001` requires intraday data. Daily OHLCV is insufficient because the hypothesis depends on:

- regular-session open;
- prior regular-session close;
- intraday VWAP;
- VWAP reclaim timing;
- opening-window volume;
- intraday holding-window return;
- spread or quote proxy.

## Status

No provider is selected by this artifact.

No provider query, network call, data download, extractor implementation, OOS run, paper/live or strategy promotion has occurred.
