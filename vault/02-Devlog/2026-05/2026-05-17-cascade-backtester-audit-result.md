# 2026-05-17 - Backtester audit result

## Contesto

Dopo [[Report-Backtester-Audit-Plan-2026-05-17]], e' stata eseguita la parte TDD mirata dell'audit su auditability del trade/rejection log.

## RED

Aggiunti due test in `tests/test_small_cap_portfolio_backtester.py`:

- `test_portfolio_backtester_trade_log_records_entry_reference_and_cost_model`
- `test_portfolio_backtester_rejection_log_records_planner_diagnostics`

Il RED ha mostrato che:

- il trade log non conservava `entry_reference_price`;
- le rejection da planner non conservavano diagnostiche come `entry_reference_price` e `next_open_gap_pct`.

## GREEN

Fix in `src/backtest/small_cap_portfolio_backtester.py`:

- aggiunto `entry_reference_price` alle trade rows;
- aggiunta funzione `_decision_diagnostics` e forwarding delle diagnostiche planner nelle rejection rows.

Test mirati:

```text
28 passed
```

## Report

Creato [[Report-Backtester-Audit-Result-2026-05-17]].

Verdict:

```text
TECHNICAL_PASS_WITH_LIMITATIONS
```

## Governance

Questo migliora auditabilita' backtester, ma non apre trial small-cap. Restano attivi data/provider gate, methodology ledger e no paper trading.
