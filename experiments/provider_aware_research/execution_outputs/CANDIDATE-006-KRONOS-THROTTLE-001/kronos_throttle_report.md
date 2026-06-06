# Candidate 006 Kronos Throttle 001

Decision: `CANDIDATE_006_KRONOS_THROTTLE_COMPLETE_NO_PROMOTION`

Scope: fixed half-size risk throttle diagnostic only. No new inference, no sweep, no promotion.

## Baseline Versus Binary Versus Throttle

- Baseline trades: `37`
- Full-weight trades: `11`
- Half-weight trades: `26`
- Baseline weighted net: `0.14726152684605037`
- Binary overlay weighted net: `0.05342042500865488`
- Throttle weighted net: `0.10034097592735262`
- Throttle minus baseline: `-0.04692055091869775`
- Throttle minus binary overlay: `0.04692055091869774`
- Baseline max drawdown: `-0.029435952071681024`
- Binary overlay max drawdown: `-0.0003614772957769002`
- Throttle max drawdown: `-0.014698712983787526`

## Same-Reduced-Count Random Baseline

- Iterations: `1000`
- Random weighted net median: `0.09525434405037497`
- Random weighted net p95: `0.11873527643813031`
- Observed weighted net percentile: `0.63`

## Interpretation

- The half-size throttle recovered return versus the binary keep/reject overlay.
- The throttle reduced local drawdown versus the unthrottled baseline.
- The fixed Kronos throttle did not decisively beat same-reduced-count random throttles.

## Blockers

- `diagnostic_only_no_promotion`
- `single_archived_panel_only`
- `random_same_reduced_count_baseline_not_decisively_beaten`
