# XMOM pre-run gate summary

```text
XMOM_PRE_RUN_GATE_SPEC_ONLY
NOT_EXECUTED
FAIL_CLOSED
ON_ANY_CHECK_FAIL -> EXIT 1
```

This artifact defines the hard pre-run gate for `TRIAL-XMOM-001`.

Execution is blocked unless all required checks are `PASS`:

1. `databento_data_exists`
2. `config_hash_match`
3. `ledger_status_is_prepared`

If any required check is missing, unresolved, or fails validation:

- process returns `EXIT 1`;
- no provider query is allowed;
- no backtest is allowed;
- no strategy promotion is allowed.

This is a gate-definition artifact only and does not authorize execution.
