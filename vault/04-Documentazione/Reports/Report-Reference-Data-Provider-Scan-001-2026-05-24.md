# Report Reference Data Provider Scan 001 - 2026-05-24

Decision: `REFERENCE_DATA_PROVIDER_SCAN_COMPLETE_PROBE_CANDIDATE_SELECTED`

## Scope

Documentation scan only. No provider API query, market-data download, strategy backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.

## Result

- Providers scanned: 5
- Probe candidates: 1
- Recommended next probe: Polygon/Massive

## Scorecard

- Polygon/Massive: status=PROBE_CANDIDATE score=44 pit=pass delisted=pass exchange=pass type=pass source=https://polygon.io/docs/rest/stocks/tickers/all-tickers
- Sharadar/Nasdaq Data Link: status=BLOCKED_REFERENCE_METADATA_INSUFFICIENT score=42 pit=pass delisted=pass exchange=pass type=pass source=https://www.sharadar.com/data
- Intrinio Securities: status=NEEDS_ENTITLEMENT_VERIFICATION score=27 pit=maybe delisted=maybe exchange=pass type=pass source=https://docs.intrinio.com/documentation/web_api/get_all_securities_v2
- Tiingo: status=BLOCKED_REFERENCE_METADATA_INSUFFICIENT score=13 pit=maybe delisted=maybe exchange=maybe type=maybe source=https://www.tiingo.com/documentation/general/overview
- SEC company_tickers: status=BLOCKED_REFERENCE_METADATA_INSUFFICIENT score=3 pit=fail delisted=fail exchange=fail type=fail source=https://www.sec.gov/files/company_tickers.json

## Next Step

Preregister a single provider-specific source probe for the selected provider; do not download market data or run a strategy.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
