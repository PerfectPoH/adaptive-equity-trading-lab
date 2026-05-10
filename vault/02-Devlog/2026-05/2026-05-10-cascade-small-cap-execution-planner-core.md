---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-execution-planner-core
tags: [devlog, small-cap, execution, portfolio, tdd]
---

# 2026-05-10 - Small-Cap Execution Planner Core

## Contesto

Dopo il report diagnostico arricchito, il limite principale rimaneva il proxy holding-window: i candidati operativi venivano valutati senza un ledger di capitale, cash disponibile e posizioni sovrapposte.

Il primo passo verso un portfolio backtester reale e' un planner atomico:

```text
candidate + next_open + available_cash -> execution decision
```

## Cosa e' stato aggiunto

Nuovo modulo:

```text
src/backtest/small_cap_execution_planner.py
```

Nuovo test:

```text
tests/test_small_cap_execution_planner.py
```

## API

```text
SmallCapExecutionPlanner
SmallCapExecutionDecision
```

`SmallCapExecutionPlanner` riusa `SmallCapExecutionConfig`, quindi rimane coerente con le regole gia' usate dal candidate export.

## Regole coperte

Il planner atomico gestisce:

```text
next-open gap reject
entry cost haircut: spread_bps + slippage_bps
capacity cap: avg_dollar_volume_20d * max_position_dollar_volume_fraction
cash cap: available_cash
min_trade_notional
fail-closed su dati mancanti
```

## Test TDD aggiunti

```text
test_execution_planner_rejects_next_open_gap_above_limit
test_execution_planner_caps_notional_by_dollar_volume_capacity
test_execution_planner_caps_notional_by_available_cash
test_execution_planner_applies_entry_cost_haircut
test_execution_planner_rejects_when_cash_is_below_min_notional
```

## Verification mirata

```text
python -m pytest tests/test_small_cap_execution.py tests/test_small_cap_execution_planner.py
11 passed
```

## Perche' e' importante

Questo modulo e' il ponte tra scanner e portfolio backtester. Permette di testare la logica execution senza ancora introdurre complessita' di:

```text
open positions
cash ledger
holding periods
max concurrent trades
triage giornaliero
```

## Prossima mossa

Costruire `SmallCapPortfolioBacktester` sopra il planner:

```text
candidate_export + frames + initial_cash
-> trade_log
-> equity_curve
-> rejection_summary
```

Vedi [[small-cap-swing-research-spec]], [[2026-05-10-cascade-small-cap-report-diagnostics]], [[Roadmap-Master]].
