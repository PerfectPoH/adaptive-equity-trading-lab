---
tipo: audit-result
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: TECHNICAL_PASS_WITH_LIMITATIONS
scope: backtester_methodology_gate
---

# Report Backtester Audit Result - 2026-05-17

## Status

```text
BACKTESTER AUDIT: TECHNICAL_PASS_WITH_LIMITATIONS
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This audit executed the targeted TDD portion of [[Report-Backtester-Audit-Plan-2026-05-17]].

## Scope executed

The audit focused on mechanics already covered by existing tests plus two missing auditability properties:

1. portfolio trade log must preserve planner `entry_reference_price`;
2. rejection log must preserve planner diagnostics for planner-level rejections.

## RED result

New tests were added to `tests/test_small_cap_portfolio_backtester.py`:

- `test_portfolio_backtester_trade_log_records_entry_reference_and_cost_model`
- `test_portfolio_backtester_rejection_log_records_planner_diagnostics`

Initial targeted run failed because:

- trade log did not include `entry_reference_price`;
- planner rejection rows did not include `entry_reference_price`, `next_open_gap_pct` and related diagnostics.

This was a valid RED signal for auditability, not a strategy failure.

## Fix applied

`src/backtest/small_cap_portfolio_backtester.py` now:

- writes `entry_reference_price` into accepted trade rows;
- forwards planner diagnostics into rejection rows via `_decision_diagnostics`.

Diagnostics forwarded:

- `entry_reference_price`
- `entry_price`
- `estimated_cost_pct`
- `next_open_gap_pct`
- `stop_loss`
- `take_profit`
- `max_liquidity_notional`
- `position_size`
- `position_notional`

## GREEN result

Targeted tests passed:

```text
28 passed
```

Targeted command:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_execution_planner.py -q
```

## Coverage matrix

| Fixture area | Status | Evidence |
|---|---|---|
| Risk-fraction sizing | pass | `test_execution_planner_uses_risk_fraction_position_sizing_before_cash_or_liquidity_caps` |
| Cash ledger timing | pass | cash locked/released tests in `test_small_cap_portfolio_backtester.py` |
| Entry/exit bar mechanics | pass | entry/exit date and missing holding-window tests |
| Cost model auditability | pass | new trade-log entry reference/cost test |
| Planner rejection diagnostics | pass | new rejection diagnostics test |
| Missing price path | pass | `missing_price_path` rejection test |
| Max concurrent positions | pass | `max_concurrent_positions` rejection test |
| Same-day ranking/tie-breaks | pass | RankEx tie-breaker test |
| Filters/regime gates | pass | setup, feature and regime rejection tests |
| Rejection summary | pass | existing rejection summary assertions |
| Equity curve reconciliation | pass | open-position equity and final cash tests |

## Known limitations

The audit does not promote the backtester to production execution realism. The following limitations remain explicit:

- exit slippage/costs are not separately modeled;
- intraday stop-loss/take-profit execution is not modeled;
- partial fills are not modeled;
- halt/non-tradable bars require better provider/event data;
- corporate-action interpretation depends on upstream data provider.

These limitations must be repeated in any future strategy preregistration that depends on this backtester.

## Verdict

```text
TECHNICAL_PASS_WITH_LIMITATIONS
```

The backtester is sufficiently auditable for methodology work after this fix, but this does not unlock small-cap trials by itself.

## Governance consequence

This result satisfies the immediate RISK-043 auditability gap for documented mechanics. Future small-cap trials remain blocked by data/provider and broader methodology gates.
