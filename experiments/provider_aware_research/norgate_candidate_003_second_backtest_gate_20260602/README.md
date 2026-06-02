# Norgate Candidate 003 Second Backtest Gate 001

This gate authorizes exactly one second Candidate 003 backtest on the frozen representative Norgate universe.

The representative universe passed minimum panel requirements:

- accepted active symbols: `159`
- accepted delisted symbols: `123`
- accepted non-benchmark symbols: `282`
- required benchmarks: `SPY`, `IWM`

## What This Gate Allows

- One Candidate 003 second backtest.
- Daily adjusted OHLCV provider queries for the frozen accepted symbols only.
- Benchmark queries for `SPY` and `IWM`.
- Raw artifact retention.

## What This Gate Does Not Allow

- Universe rebuild.
- Symbol replacement.
- Parameter sweep.
- Weight optimization.
- Cost change.
- Holding-period change.
- Lookback change.
- Component change.
- Promotion.
- Paper trading.
- Live trading.
- Any durable financial performance claim.

## Frozen Behavior

The dollar-bar sleeve remains disabled/idle because Norgate daily bars cannot reconstruct dollar bars. Its weight is not redistributed.

The active daily sleeves are:

- Momentum, weight `0.25`.
- Mean Reversion, weight `0.25`.
- Momentum, weight `0.25`.

The inactive sleeve is:

- Dollar-Bar Microstructure, idle weight `0.25`.

## Next Allowed Action

`run_candidate_003_second_backtest_once`

If the second run fails the hard archive conditions, Candidate 003 remains archived until a broader/full-history data source or a newly preregistered candidate exists.
