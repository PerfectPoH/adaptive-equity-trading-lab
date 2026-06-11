# Trade Governance Runtime - 2026-05-21

Implemented `src.execution.trade_governance` as broker-free execution governance infrastructure.

## Added

- `GOOD_WIN / GOOD_LOSS / BAD_WIN / BAD_LOSS` classification.
- Governed metrics that remove profitable protocol violations from edge metrics.
- Same-symbol cooldown after stop-loss exit.
- Cooldown exception for attempted re-entry during lockout.
- Spec artifacts for trade quality, cooldown and PnL display policy.

## Verification

- Targeted test file: `tests/test_trade_governance.py`.

## Decision

`TRADE_GOVERNANCE_RUNTIME_IMPLEMENTED_SPEC_ONLY`.

No provider query, broker connection, backtest, paper/live trading or strategy promotion was performed.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
