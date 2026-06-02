# Norgate Candidate 003 Micro-Backtest Gate 001

This gate authorizes exactly one bounded, trial-limited micro-backtest for `PORTFOLIO-CANDIDATE-003-MANUAL-COMPOSITE` using the locally installed Norgate Data trial.

The gate is allowed only because `NORGATE-CANDIDATE-003-SCHEMA-PROBE-001` confirmed:

- Python package access.
- `US Equities` active database access.
- `US Equities Delisted` database access.
- listing and delisting metadata.
- historical constituent watchlists.
- adjusted daily price access.

## What This Gate Allows

- One Candidate 003 micro-backtest run.
- Local Norgate provider queries for deterministic active/delisted symbol selection.
- Daily adjusted OHLCV retrieval for trial-selected symbols and benchmarks.
- Raw payload/artifact retention.

## What This Gate Does Not Allow

- Promotion.
- Paper trading.
- Live trading.
- Short selling.
- Parameter sweeps.
- Strategy combination search.
- Weight optimization.
- Component replacement after seeing results.
- Any durable financial performance claim.

## Frozen Candidate Behavior

The frozen operational contract is the 4-component manual composite, not the older 3-sleeve descriptive summary:

- Mean Reversion: active, weight 0.25.
- Momentum component `28fb7b03aa56a91e`: active, weight 0.25.
- Momentum component `acc065823d9dcfb7`: active, weight 0.25.
- Dollar-Bar Microstructure: disabled/idle, weight 0.25, because daily Norgate bars cannot reconstruct dollar bars.

Disabled sleeve weight is not redistributed. Reallocation after discovering missing data would mutate the candidate and create a new overfitting channel.

## Trial Limitation

The Norgate free trial is expected to provide roughly two years of history. Any result from the authorized micro-backtest must remain diagnostic and non-promotable.

Next allowed action: `run_candidate_003_micro_backtest_once`.
