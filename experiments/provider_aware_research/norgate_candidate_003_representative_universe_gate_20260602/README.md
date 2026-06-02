# Norgate Candidate 003 Representative Universe Gate 001

This gate responds to the Candidate 003 post-mortem. The first Norgate micro-backtest was not representative because the loader selected the first common-like symbols that survived data checks, producing an alphabetically biased `A*` panel.

This gate does **not** authorize another portfolio backtest.

It authorizes exactly one representative-universe construction pass.

## What This Gate Allows

- One Norgate representative-universe build.
- Historical watchlist lookup from the frozen watchlist contract.
- Active and delisted database resolution.
- Listing and delisting metadata lookup.
- Adjusted daily OHLCV retrieval only for the preselected universe-validation symbols.
- Raw artifact retention.

## What This Gate Does Not Allow

- Candidate 003 rerun.
- Promotion.
- Paper trading.
- Live trading.
- Short selling.
- Parameter sweeps.
- Weight optimization.
- Symbol replacement after seeing prices.
- Any financial performance claim.

## Frozen Universe Logic

Primary watchlist:

- `Russell 2000 + Micro Cap Superset Current & Past`

The selection must avoid raw ticker ordering. It must use stable hash sampling by symbol and bucket, with active and delisted names both represented.

The tradability filter remains frozen:

- minimum price: `1.0`
- minimum median turnover: `1000000.0`
- minimum rows: `90`

Minimum panel requirements before a second backtest gate can even be considered:

- accepted active symbols: at least `40`
- accepted delisted symbols: at least `40`
- accepted total symbols: at least `100`
- required benchmarks: `SPY`, `IWM`

## Next Allowed Action

`build_candidate_003_representative_universe_once`

If the representative panel fails these requirements, Candidate 003 remains archived until a broader/full-history data source is available.
