# Report Polygon Listing Date Coverage Probe 001 - 2026-05-24

Decision: `POLYGON_LISTING_DATE_COVERAGE_SUPPORT_BLOCKED`

## Scope

Bounded Polygon/Massive ticker details reference calls for ten active seed tickers. Only derived listing-date metadata retained. No market-data download, backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.

## Result

- Expected tickers: 10
- Provider calls: 10
- Provider successes: 5
- Provider errors: 5
- Detail successes: 5
- List-date present count: 5
- List-date coverage: 0.5
- Blockers: detail_success_count_below_8, list_date_coverage_below_0_80

## Interpretation

This probe only tests bounded listing-date coverage. It does not authorize PIT universe construction or broad-universe backtests.
