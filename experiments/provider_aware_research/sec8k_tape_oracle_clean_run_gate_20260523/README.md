# SEC8K Tape Oracle Clean Run Gate

Status: APPROVED_PRE_RUN_NOT_EXECUTED

This gate authorizes one bounded Databento acquisition and backtest for
`SEC8K-TAPE-ORACLE-CLEAN-RUN-002`.

The invalidated `SEC8K-TAPE-ORACLE-DATABENTO-MINI-PANEL-001` run may remain in
the repository as audit trail only. It must not be used for thresholds,
calibration, symbol selection, evidence, or promotion.

The run is allowed to test only the pre-registered long-only positive tape
oracle:

- SEC 8-K Item 2.02 event days only
- First 15 minute RTH oracle window
- Entry at 09:46 America/New_York
- Flat by 15:55 America/New_York
- Volume ratio threshold fixed at 3.0
- Cost realism fixed at 500 bps
- No parameter sweep
- No paper trading
- No live trading
- No promotion in this run
