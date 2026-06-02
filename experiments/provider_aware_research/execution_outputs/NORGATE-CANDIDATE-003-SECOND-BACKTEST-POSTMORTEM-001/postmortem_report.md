# Candidate 003 Second Backtest Post-Mortem 001

Decision: `CANDIDATE_003_ARCHIVE_RESEARCH_LEAD_ONLY`

Scope: existing second-backtest artifacts only. No provider query, no new backtest, no market-data download, no promotion.

## What Worked

- Representative panel loaded: `282` / `282` non-benchmark symbols.
- Weighted net return was positive: `0.490214`.
- Benchmark relative was positive versus SPY `0.018066` and IWM `0.046280`.

## Why It Still Failed

- Ex-best-symbol net was negative: `-0.141806` after removing `TERN-202605`.
- Win rate stayed weak: `0.3770`.
- Two active Momentum components produced identical weighted contribution, so the portfolio was not genuinely diversified.
- Dollar-Bar Microstructure remained disabled because Norgate daily OHLCV cannot reconstruct dollar bars.
- Trial history remains too short for a durable claim.

## Candidate 004 Implication

Candidate 004 must not be a parameter tweak of Candidate 003. It should be a new architecture:

- one Momentum sleeve, not two;
- one Mean Reversion sleeve, but only where regime diagnostics permit it;
- one daily-compatible Defensive/Low-Vol sleeve;
- one Cash/No-Trade sleeve that can intentionally suppress trading;
- a frozen regime router that decides sleeve eligibility before any backtest.