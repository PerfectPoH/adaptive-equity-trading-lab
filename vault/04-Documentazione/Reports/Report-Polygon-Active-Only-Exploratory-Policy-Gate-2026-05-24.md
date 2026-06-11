# Report Polygon Active-Only Exploratory Policy Gate - 2026-05-24

Decision: `POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_ALLOWED_NO_PROMOTION`

## Scope

No-query governance gate for active-only exploratory research after the delisted listing-date blocker. No provider query, market-data download, strategy backtest, execution, short selling, or promotion occurred.

## Authorization

- Active-only exploratory research allowed: True
- Survivorship-free claim allowed: False
- Strategy promotion allowed: False
- Broad survivorship-free backtest allowed: False
- Mandatory caveats: active_only_survivorship_bias_declared, no_survivorship_free_claim, no_strategy_promotion, no_live_or_paper_trading, exploratory_research_only

## Interpretation

The current free Polygon stack may support explicitly caveated active-only exploratory trials, but it cannot support survivorship-free broad-universe alpha claims or promoted strategies without delisted listing-date coverage.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
