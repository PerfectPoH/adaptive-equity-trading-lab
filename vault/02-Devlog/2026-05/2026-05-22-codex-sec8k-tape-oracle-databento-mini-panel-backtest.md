# Report SEC8K Tape Oracle Databento Mini Panel Backtest - 2026-05-22

Decision: `SEC8K_TAPE_ORACLE_MINI_PANEL_NO_PROMOTION_COST_AND_SAMPLE_BLOCKED`

## Scope

Bounded Databento mini-panel for SEC 8-K Tape Oracle. Raw payloads were not retained. No parameter sweep, paper/live trading, or promotion occurred.

## Data

- Query count: 30
- Pass count: 30
- Empty count: 0
- Error count: 0

## Backtest

- Evaluated event count: 30
- Positive oracle trade count: 4
- Gross return sum: 0.0505549675
- Net return sum after 500 bps: -0.1494450325
- Blockers: positive_oracle_trade_count_below_30

## Interpretation

This is the first bounded live-data expansion of the SEC8K Tape Oracle branch. The result remains non-promotable unless sample size, costs, and statistical gates pass.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
