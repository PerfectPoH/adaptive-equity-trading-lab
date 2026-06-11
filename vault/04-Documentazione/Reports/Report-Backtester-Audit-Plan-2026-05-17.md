---
tipo: audit-plan
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: SPEC_ONLY_NOT_EXECUTED
scope: backtester_methodology_gate
---

# Report Backtester Audit Plan - 2026-05-17

## Status

```text
SPEC ONLY / NOT EXECUTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document defines the TDD audit plan for `SmallCapPortfolioBacktester` and related execution-planning mechanics before any future strategy interpretation.

## Background

`BUG-037` showed that a single portfolio mechanic can materially change results: the execution planner previously ignored `risk_fraction` and allocated near all available cash to a trade, causing cash starvation and distorted OOS results.

That bug has been fixed with TDD, but RISK-043 remains: other backtester mechanics can still bias future results if they are not explicitly audited.

## Objective

Verify that the portfolio backtester behaves mechanically and reproducibly under adversarial fixtures before any future small-cap trial uses it as evidence.

## Non-goals

- Do not evaluate alpha.
- Do not run any strategy trial.
- Do not tune scanner thresholds.
- Do not run OOS.
- Do not change portfolio policy during this audit unless a bug is proven by a failing test.

## Audit scope

| Area | Risk | Required outcome |
|---|---|---|
| Risk-fraction sizing | position size silently ignores stop risk | position size equals risk-based size capped by liquidity and cash |
| Cash ledger timing | capital released too early or too late | cash locked from entry until exit; same-day release policy explicit |
| Entry/exit price path | entry or exit uses wrong bar | signal date, next open entry and holding-period exit are deterministic |
| Slippage/spread cost | costs applied inconsistently | entry cost haircut is explicit and reflected in trade log |
| Open positions at period end | open trades are dropped or marked inconsistently | forced closure or rejection policy is explicit and tested |
| Calendar/holidays | non-business gaps distort holding period | holding period uses available bars, not calendar guesses |
| Missing price path | partial OHLCV produces silent trades | missing path rejected with `missing_price_path` and no cash spend |
| Max concurrent positions | portfolio overfills beyond cap | rejections preserve available cash and reason |
| Insufficient funds | candidate rejected incorrectly or cash goes negative | no negative cash; rejection ledger records reason and available cash |
| Candidate ranking | same-day candidates processed nondeterministically | ranking and tie-break behavior deterministic |
| Filters/regime gates | filtered candidates affect cash incorrectly | filtered/setup/regime rejections do not spend cash |
| Rejection ledger | failure reasons lost | all non-trade decisions are auditable |
| Equity curve | equity rows mismatch cash/open positions | equity curve reconciles with trade log and ending cash |

## Required TDD fixtures

The audit should add or verify explicit tests for each fixture class.

### Fixture A - Risk sizing reconciliation

Expected checks:

- `position_size = min(risk_size, liquidity_size, cash_size)`;
- `risk_size` uses `calculate_position_size(available_cash, entry_price, stop_loss, risk_fraction)`;
- lowering `risk_fraction` lowers notional;
- liquidity cap can bind;
- cash cap can bind;
- below-min-notional candidates reject without spending cash.

### Fixture B - Cash release ordering

Expected checks:

- cash is locked after entry;
- cash is released on exit date before later same-day candidates are evaluated;
- cash is not released before exit date;
- losing trades reduce available cash after exit;
- winning trades increase available cash after exit;
- no negative cash appears in trade log or equity curve.

### Fixture C - Entry/exit bar mechanics

Expected checks:

- signal on `T` enters at next available open;
- exit occurs after `holding_period_bars` available bars;
- missing next open rejects;
- missing exit close rejects;
- non-contiguous calendar days still count by bars;
- last-window candidates without enough future bars reject.

### Fixture D - Cost model

Expected checks:

- `entry_price = next_open * (1 + (spread_bps + slippage_bps) / 10000)`;
- trade log stores `estimated_cost_pct`;
- cash after entry uses cost-adjusted entry price;
- PnL uses cost-adjusted entry price and raw configured exit price unless an explicit exit-cost policy is introduced;
- if exit costs are not modeled, report must state this limitation.

### Fixture E - Concurrent candidates and ranking

Expected checks:

- same-day candidates sort by configured rank column;
- `small_cap_scanner_score` tie-breaks are deterministic;
- `max_concurrent_positions` rejection happens before cash spend;
- accepted first candidate can reduce cash for later same-day candidates;
- rejection ledger preserves same-day ordering evidence.

### Fixture F - Filters and regime gates

Expected checks:

- `allowed_setups` rejection does not spend cash;
- `feature_filters` rejection records filter metadata;
- `regime_filters` rejection records filter metadata;
- filtered benchmark candidate export and portfolio backtester use compatible filter semantics.

### Fixture G - Rejection ledger integrity

Expected checks:

- every rejection has `symbol`, `as_of`, `reject_reason`, `available_cash`;
- known reasons are enumerated or tested;
- missing data rejects before planner spending;
- empty rejection file is valid when there are zero rejections;
- rejection summary equals value counts of rejection ledger.

### Fixture H - Equity curve reconciliation

Expected checks:

- final equity row equals `summary.ending_cash` when no open positions remain;
- open position notional equals sum of open position notionals;
- open position count equals open position list length;
- total PnL equals sum of trade log PnL;
- return_pct equals `(ending_cash / initial_cash) - 1`.

## Existing coverage to preserve

Existing tests already cover parts of the audit and should be preserved:

- risk-fraction sizing in `SmallCapExecutionPlanner`;
- cash lock/release timing;
- same-day exit release before later candidate;
- missing price path rejection;
- max concurrent positions;
- gap rejection;
- empty/no-trade cases;
- NCTRL cash-ledger property gate.

The audit execution should map each existing test to the fixture matrix and add missing tests only where gaps remain.

## Expected limitations to document

If these remain by design, the audit result must explicitly document them:

- exit slippage/costs may not be modeled;
- intraday stop-loss/take-profit execution may not be modeled;
- partial fills may not be modeled;
- halt/non-tradable bars may require provider/event data beyond the backtester;
- corporate-action-adjusted price interpretation depends on data provider.

A limitation can be acceptable only if it is documented and not material to the proposed future trial.

## Acceptance gates

The audit may pass only if:

```text
all existing backtester tests pass
all new fixture tests pass
no known cash ledger inconsistency remains
risk_fraction sizing remains capped by risk/liquidity/cash
artifact validator passes on any run used as evidence
limitations are documented before any trial preregistration
```

## Failure gates

The audit fails and blocks future strategy interpretation if any of these occur:

```text
cash can go negative without explicit leverage model
positions can exceed max_concurrent_positions
rejections spend cash
trade log PnL does not reconcile to ending cash
entry/exit dates are ambiguous under missing bars
risk_fraction is bypassed in any portfolio path
```

## Recommended execution order

1. Create a test coverage matrix from existing tests.
2. Add RED tests for missing fixture classes only.
3. Fix root causes, not outputs.
4. Run targeted backtester/planner tests.
5. Run full suite.
6. Write audit result report with pass/fail and limitations.
7. Update Methodology Gate Ledger.

## Future output

The execution of this plan should produce:

```text
Report-Backtester-Audit-Result-YYYY-MM-DD.md
```

The result must include:

- coverage matrix;
- new tests added;
- bugs found/fixed;
- known limitations;
- pass/fail verdict;
- impact on future small-cap trial eligibility.

## Current decision

This audit plan is now specified but not executed.

Before any new small-cap strategy trial, the project must either execute this plan or document why the future trial does not depend on `SmallCapPortfolioBacktester` mechanics.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
