# Public Catalyst Tradable-Only Strict Micro-Backtest 001

Input panel: `tradable_only_event_panel.csv`

As-of enforcement date: `2026-06-01`

- decision: `PUBLIC_CATALYST_HYBRID_MICRO_BACKTEST_COMPLETE_EXPLORATORY_ONLY`
- events in panel: `18`
- events with local price coverage: `18`
- trades: `54`
- weighted net return sum: `0.926564`
- win rate: `0.5926`
- max drawdown: `-0.897241`
- loaded local symbols: `18`
- price failures: `0`

## Blockers

- `manual_panel_non_promotable`
- `coverage_completeness_not_proven`
- `delisted_retention_not_proven`

This is exploratory only. No promotion, paper trading, live trading, or durable performance claim is allowed.

## Tradable-Only Filter

- Source panel rows: `34`
- Kept events: `18`
- Excluded events: `16`
- Kept symbols: `AGIO, AQST, ASND, CAPR, CING, DNLI, FBIO, GKOS, KALV, MIST, OTLK, PTCT, RARE, REPL, SNDX, SUPN, TNXP, UNCY`

This run removes private/nonstandard symbols, unavailable local price coverage, acquired/delisted/renamed rows, partial date-aware mappings, and event dates after 2026-06-01.


## Robustness Check

- Total weighted net: `0.926564`
- Ex-top1 weighted net: `-0.435825`
- Ex-top3 weighted net: `-0.959596`
- Top event contribution share: `147.04%`
- Top 3 contribution share: `203.57%`
- Robustness diagnostic: `TRADABLE_ONLY_ROBUSTNESS_DIAGNOSTIC_BLOCK_PROMOTION`

This check is intentionally hostile: the sleeve is not considered robust if the result depends on a tiny set of event winners.
