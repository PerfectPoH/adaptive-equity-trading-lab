# Report Polygon PIT Construction Method Gate - 2026-05-24

Decision: `POLYGON_PIT_CONSTRUCTION_METHOD_APPROVED_PARTIAL_SAMPLE_ONLY`

## Scope

No-query method gate using archived derived metadata only. It builds a sample PIT membership table to validate the as-of rule, but it does not build a full PIT universe and does not authorize any strategy backtest.

## Method

`list_date <= as_of_date < delisted_date`

## Result

- Listing-date sample count: 10
- Delisted reference sample count: 10
- Membership row count: 20
- Member counts by as-of date: {'2024-01-02': 7, '2026-05-22': 10}
- Broad backtest allowed: False
- Broad backtest blockers: sample_only_method_gate, delisted_listing_dates_unavailable_for_full_pit, full_historical_membership_artifact_unbuilt, strategy_trial_not_preregistered

## Interpretation

The PIT construction method is approved only at sample level. The next step must be a separately preregistered full-universe PIT artifact build; no broad strategy backtest is authorized by this gate.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
