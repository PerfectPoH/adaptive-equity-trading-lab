# Portfolio Component Coverage Gate 001

## Verdict

`FULL_PORTFOLIO_JUDGMENT_BLOCKED_BY_COMPONENT_COVERAGE`

The tradability-filtered Norgate rerun does not falsify Portfolio Candidate 002 as a complete four-sleeve design. It falsifies only the daily-compatible subset that Norgate can observe under the current trial:

- Momentum
- Mean Reversion

The other two sleeves were not tested:

- Catalyst
- Dollar-Bar Microstructure

## Why this matters

The portfolio was designed to self-balance across different evidence types. If two evidence types are disabled, the run becomes a two-sleeve daily strategy, not the original candidate.

The lab must therefore prevent two errors:

1. Calling the full portfolio dead when only half of it had admissible data.
2. Redistributing disabled sleeve weights and pretending the four-sleeve design was evaluated.

## Provider map

Norgate is admissible for survivor-aware daily equity research, active/delisted coverage, historical constituents, and quote-date metadata. It is not intended to reconstruct intraday dollar bars or supply point-in-time catalyst direction.

The full candidate needs a provider stack:

- Norgate or CRSP for survivor-aware daily prices and delisting-aware history.
- Databento, NYSE TAQ, WRDS TAQ, or Nasdaq TotalView/ITCH for intraday trades, quotes, and order-book reconstruction.
- I/B/E/S, FactSet PIT Estimates, Zacks/Sharadar-style paid feeds, or equivalent for point-in-time earnings direction.
- BioMedTracker/Citeline/Evaluate-style data for biotech catalyst calendars and context.

## Next rule

No full portfolio promotion, rejection, or live/paper deployment is allowed until every component has an admissible data contract.
