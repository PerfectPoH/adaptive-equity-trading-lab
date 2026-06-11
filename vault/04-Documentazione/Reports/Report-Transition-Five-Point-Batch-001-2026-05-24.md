# Report Transition Five Point Batch 001 - 2026-05-24

Decision: `TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY`

## Scope

Executed the five next-step diagnostics using existing local artifacts only. No provider query, market-data download, new strategy backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.

## Five Points

- ETF/large-cap regime rows: 20990
- Risk overlay archived trades: 44
- Portfolio allocation smoke symbols: 10
- Small-cap microstructure symbols: 6
- Data upgrade tracks: 4

## Risk Overlay

- Original archived net sum: 1.98092434
- Overlay net sum: -0.38795234
- Fragility block: True

## Data Decision

- smallcap_directional_free_data: PAUSE - active_only_survivorship_bias_and_top3_dependency
- pit_universe_data: BLOCKED - delisted_listing_dates_unavailable_for_full_pit
- etf_largecap_risk_regime_lab: ALLOW_DIAGNOSTICS_ONLY - local_historical_snapshots_available_without_provider_query
- paid_data_purchase: DEFER - no_single_paid_feed_purchase_is_justified_by_current_failed_alpha_queue

## Interpretation

This batch moves the lab from directional small-cap alpha hunting toward risk/regime diagnostics. It preserves the research pause on free-data small-cap directional work and creates no tradable signal.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
