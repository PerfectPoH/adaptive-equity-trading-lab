# Report Trade Governance Runtime - 2026-05-21

Decision: `TRADE_GOVERNANCE_RUNTIME_IMPLEMENTED_SPEC_ONLY`

## Scope

Implemented a local execution-governance module for future paper/live infrastructure:

- classify trades into `GOOD_WIN`, `GOOD_LOSS`, `BAD_WIN`, `BAD_LOSS`;
- exclude `BAD_WIN` from edge metrics even when profitable;
- enforce same-symbol cooldown after stop-loss exits;
- reject timezone-naive cooldown timestamps;
- document PnL display policy for future execution interfaces.

## Artifacts

- `src/execution/trade_governance.py`
- `tests/test_trade_governance.py`
- `experiments/provider_aware_research/trade_governance_runtime_spec_20260521/trade_quality_policy.csv`
- `experiments/provider_aware_research/trade_governance_runtime_spec_20260521/cooldown_policy.csv`
- `experiments/provider_aware_research/trade_governance_runtime_spec_20260521/pnl_display_policy.csv`
- `experiments/provider_aware_research/trade_governance_runtime_spec_20260521/trade_governance_manifest.json`

## Interpretation

This is infrastructure, not alpha research. It does not query providers, connect to a broker, run a backtest, authorize paper/live trading, or promote any strategy.

The key invariant is behavioral: a profitable protocol violation is not alpha. It is excluded from governed edge metrics so the lab cannot learn from lucky rule-breaking.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
