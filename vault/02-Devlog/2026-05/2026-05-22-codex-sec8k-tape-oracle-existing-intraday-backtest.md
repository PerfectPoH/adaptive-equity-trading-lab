# Report SEC8K Tape Oracle Existing Intraday Backtest - 2026-05-22

Decision: `SEC8K_TAPE_ORACLE_ARCHIVE_CURRENT_EXISTING_DATA_FORM`

## Scope

Bounded backtest on existing intraday artifacts only. No provider query, market-data download, parameter sweep, paper/live trading, or promotion occurred.

## Result

- Evaluated SEC8K event count: 1
- Positive oracle trade count: 0
- Gross return sum: 0
- Net return sum after 500 bps: 0
- Blockers: positive_oracle_trade_count_below_30, no_positive_oracle_candidates

## Panel

- CRMD 2024-03-12: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0

## Interpretation

The existing intraday archive contains only one SEC8K-matching event, and it was purged because the fixed oracle/entry/exit windows were incomplete. This is a valid bounded backtest result, but it is not evidence against the full hypothesis; sample expansion requires a separate provider approval gate.
