# Report SEC 8-K Event Timing Diagnostic - 2026-05-22

Decision: `SEC_8K_TIMING_DIAGNOSTIC_ARCHIVE_CURRENT_FORM`

## Scope

Diagnostic-only comparison of SEC 8-K Item 2.02 event days versus non-event days using existing SEC event artifacts and existing Databento daily prices. No provider query, market-data download, backtest, parameter sweep, paper/live trading or promotion was performed.

## Result

- Event days: 7
- Control days: 975
- Event median absolute return: 0.202955665
- Control median absolute return: 0.0244988864
- Absolute-return lift: 0.1784567786
- Event median volume ratio: 3.75641665
- Control median volume ratio: 1.00298051
- Volume-ratio lift: 2.75343614
- Blockers: event_count_below_8

## Event Days

- 2025-01-07 abs_return=0.321969697 volume_ratio=5.28511688
- 2025-03-25 abs_return=0.3239308462 volume_ratio=18.12718777
- 2025-04-08 abs_return=0.0922570016 volume_ratio=3.75479985
- 2025-05-06 abs_return=0.2367256637 volume_ratio=3.03102063
- 2025-08-07 abs_return=0.09958159 volume_ratio=7.20324905
- 2025-10-20 abs_return=0.202955665 volume_ratio=3.6420552
- 2025-11-12 abs_return=0.0 volume_ratio=3.75641665

## Interpretation

This diagnostic tests only whether SEC acceptance timing marks distinguishable event windows. It does not infer earnings surprise or trade direction from future returns.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
