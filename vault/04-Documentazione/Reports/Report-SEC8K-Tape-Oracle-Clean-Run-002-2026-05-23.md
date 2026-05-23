# Report SEC8K Tape Oracle Clean Run 002 - 2026-05-23

Decision: `SEC8K_TAPE_ORACLE_CLEAN_RUN_002_ARCHIVE_COST_OR_SAMPLE_FAILED`

## Scope

Bounded Databento clean run authorized by a pre-existing gate. Raw payloads were not retained. The protocol-violated mini-panel 001 remains audit-trail only and was not used for thresholds, calibration, evidence, or promotion.

## Data

- Query count: 50
- Pass count: 50
- Empty count: 0
- Error count: 0

## Backtest

- Evaluated event count: 50
- Positive oracle trade count: 14
- Gross return sum: -0.3440212363
- Net return sum after 500 bps: -1.0440212363
- Blockers: net_return_after_500bps_not_positive, positive_oracle_trade_count_below_30

## Decision Rule

If cost or sample-size gates fail, archive without DSR/CPCV escalation. DSR/CPCV is reserved for candidates that first survive cost realism and minimum trade count.
