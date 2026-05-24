# Report Research Program Transition Policy Gate - 2026-05-24

Decision: `RESEARCH_PROGRAM_TRANSITION_ACTIVE`

## Scope

No-query governance gate transitioning the lab after the small-cap/free-data directional campaign. No market-data download, strategy backtest, execution, short selling, or promotion occurred.

## Routing

- Small-cap/free-data directional research allowed: False
- Small-cap microstructure diagnostics allowed: True
- ETF/large-cap risk/regime lab allowed: True
- Strategy promotion allowed: False
- Primary data blockers: delisted_listing_dates_unavailable_for_full_pit
- Active-only failure modes: top3_dependency, negative_ex_top3_net_return, negative_median_net_return

## Interpretation

The lab should stop retesting small-cap free-data directional alpha in its current form. Small-cap remains useful for diagnostics; ETF/large-cap is opened only for cleaner-data risk/regime research, not for easy-alpha claims.
