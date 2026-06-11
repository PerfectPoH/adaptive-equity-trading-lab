# 2026-06-07 Free Data Mesh Closure

Decision: `FREE_DATA_MESH_NOT_ADMISSIBLE_FOR_TRUE_BACKTEST`

The no-budget provider path was tested as a component-level data mesh, not as a strategy. The result is a data-readiness block, not an alpha failure.

## Provider evidence

- Tiingo is the strongest verified free component so far. It passed active, split, identity, delisted, and benchmark micro-probe checks, but it is not a complete survivorship-free/PIT universe by itself.
- EODHD key access worked, but the tested endpoints did not return valid dated adjusted OHLCV rows for the required active and delisted checks.
- FMP stable endpoints returned partial OHLCV and delisted-list evidence, but IWM and BBBY terminal checks were blocked, and adjusted OHLCV was not explicit enough for the current contract.
- Norgate Trial has the right data shape, including delisted coverage, but its two-year history is below the minimum required for the true backtest.
- Databento Historical has useful price access, but Reference entitlement is blocked for the corporate-action/security-master layer.

## Rule

Candidate 012 true backtest remains blocked until a single admissible data bundle, or a fully reconciled mesh, covers:

- point-in-time universe membership
- active and delisted adjusted OHLCV
- terminal delisted return policy
- corporate actions
- stable identifier mapping
- SPY/IWM benchmarks
- provider manifest and raw-payload hash policy

## Next posture

Keep improving Portfolio Lab, regime routing, and user strategy UX with proxy outputs clearly marked non-promotable. Do not run a true performance backtest from the free mesh until a new data-build gate points to an admissible bundle.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
