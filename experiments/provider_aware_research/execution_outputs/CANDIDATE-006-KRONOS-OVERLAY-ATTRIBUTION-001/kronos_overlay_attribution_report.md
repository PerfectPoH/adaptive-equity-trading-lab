# Candidate 006 Kronos Overlay Attribution 001

Decision: `CANDIDATE_006_KRONOS_OVERLAY_ATTRIBUTION_COMPLETE_NO_PROMOTION`

Scope: attribution diagnostic only. No new inference, no provider query, no threshold sweep, no promotion.

## Kept Versus Rejected

- Baseline trades: `37`
- Kept trades: `11`
- Rejected trades: `26`
- Kept win rate: `0.8181818181818182`
- Rejected win rate: `0.5`
- Winner capture rate: `0.4090909090909091`
- Loser rejection rate: `0.8666666666666667`
- Baseline weighted net: `0.14726152684605037`
- Overlay weighted net: `0.05342042500865488`
- Overlay minus baseline: `-0.0938411018373955`

## Same-Count Random Baseline

- Iterations: `1000`
- Random weighted net median: `0.043813871905234`
- Random weighted net p95: `0.09099664113370218`
- Observed weighted net percentile: `0.622`

## Interpretation

- Kronos kept trades had a higher win rate than rejected trades.
- The overlay rejected most losing trades in this archived panel.
- The frozen Kronos subset did not decisively beat same-count random filters.

## Blockers

- `diagnostic_only_no_promotion`
- `single_archived_panel_only`
- `kept_trade_count_below_30`
- `random_same_count_baseline_not_decisively_beaten`
- `winner_capture_rate_below_50pct`
