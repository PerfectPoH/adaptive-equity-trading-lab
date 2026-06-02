# Norgate Candidate 003 Post-Mortem 001

Decision: `NORGATE_CANDIDATE_003_POSTMORTEM_COMPLETE_NO_RERUN`

Scope: existing artifacts only. No provider query, no market-data download, no new backtest, no rerun, no promotion.

## What Happened

Candidate 003 produced a small positive weighted net return in the Norgate micro-backtest:

- total trades: `43`
- weighted net return sum: `0.105438`
- max drawdown: `-0.197706`
- win rate: `37.2%`
- best symbol: `AAL`
- best-symbol weighted net return: `0.128978`
- ex-best-symbol weighted net return: `-0.023540`

The attractive headline number is therefore not robust. Removing `AAL` flips the result negative.

## Root Cause Split

There are two separate issues.

### 1. Candidate Fragility

The strategy did not produce a broad, self-balancing portfolio result in this run.

- `AAL` contributed more than the entire net result.
- Ex-best-symbol net return was negative.
- Win rate was below 50%.
- Dollar-Bar Microstructure stayed idle because Norgate trial data is daily OHLCV and cannot reconstruct dollar bars.

This blocks promotion immediately.

### 2. Micro-Panel Construction Problem

The run was also too small and distorted to serve as a decisive falsification of the portfolio idea.

The runner requested `30` active and `30` delisted symbols, but after tradability filtering it retained only:

- `5` active symbols
- `12` delisted symbols
- `17` non-benchmark tradable symbols total

The accepted active symbols were:

- `A`
- `AA`
- `AAAU`
- `AAGIY`
- `AAL`

This is not a representative market universe. It is an alphabetically biased `A*` slice.

The tradability filter rejected:

- `25` symbols for median turnover below threshold
- `18` symbols for minimum price below threshold

The panel is therefore not just small; it is structurally biased by the deterministic first-symbol scan.

## What This Means

This result is evidence against promotion, not a clean final death sentence for the portfolio concept.

Candidate 003 failed the micro-backtest gates because the positive result depended on `AAL`, but the micro-backtest itself was not representative enough to answer the broader question: whether a frozen multi-sleeve portfolio can survive on a survivorship-aware, tradability-filtered universe.

## What Not To Do

Do not rerun by changing:

- cost assumptions
- holding periods
- ranking lookbacks
- turnover threshold
- selected symbols after seeing this result
- sleeve weights

That would turn the post-mortem into overfitting.

## Next Allowed Actions

There are only two clean paths:

1. Create a new `representative_norgate_universe_gate` that freezes a better symbol-selection method before any second run.
2. Archive Candidate 003 until full-history, broader provider data is available.

Recommended next step: create the representative-universe gate.

The gate should freeze the selection method, not tune strategy parameters. A valid design would sample across a historical constituent watchlist, keep active and delisted names, enforce tradability, and cap per-symbol/sleeve dominance. It must remain trial-limited and non-promotable.
