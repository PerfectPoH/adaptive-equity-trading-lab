# Report Polygon Universe Quality Probe 001 - 2026-05-24

Decision: `POLYGON_UNIVERSE_REFERENCE_QUALITY_BLOCKED`

## Scope

Single bounded Polygon/Massive active ticker reference call. Only derived candidate rows and aggregate quality metrics retained. No market-data download, backtest, parameter sweep, paper/live trading, or promotion occurred.

## Result

- Records observed: 1000
- Candidate active common stocks on XNAS/XNYS/XASE: 524
- Metadata coverage: {"active": 1.0, "delisted_utc": 0.0, "primary_exchange": 1.0, "ticker": 1.0, "type": 1.0}
- Blockers: metadata_coverage_below_0_95:delisted_utc

## Interpretation

This probe only decides whether Polygon/Massive reference metadata can seed a future bounded liquidity probe. It does not create a final investable universe and does not authorize strategy tests.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
