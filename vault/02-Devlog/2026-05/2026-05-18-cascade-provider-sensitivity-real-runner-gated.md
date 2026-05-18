# Devlog - Provider sensitivity real runner gated - 2026-05-18

Added a blocked `--real-run` gate report mode to `src/experiments/provider_sensitivity_diagnostic_runner.py`.

```text
REAL_RUN_BLOCKED_BY_GATES
NO_PROVIDER_QUERY
NO_BACKTEST
NO_STRATEGY_PROMOTION
```

The mode returns `real_run_gates_unresolved` and requires explicit approval, immutable output directory creation, trial ledger entry creation, credential check without provider query, and final command review before execution can be considered.

Manual and dry-run preflight artifacts now mark the runner as `real_runner_gated`; aggregate preflight remains blocked.
