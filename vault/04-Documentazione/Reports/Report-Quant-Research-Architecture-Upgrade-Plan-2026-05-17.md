---
tipo: architecture-upgrade-plan
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: SPEC_ONLY_NOT_IMPLEMENTED
scope: quant_research_framework_upgrade
---

# Report Quant Research Architecture Upgrade Plan - 2026-05-17

## Status

```text
SPEC ONLY
NOT IMPLEMENTED
NO PROVIDER QUERY
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
NO LIVE / NO PAPER TRADING
```

## Purpose

This report converts the external critique into an implementation roadmap for upgrading the project from a rigorous batch research framework into a more production-aware quantitative research platform.

The goal is not to declare the current system production-ready. The goal is to identify the missing layers that separate robust falsification research from capital-deployment infrastructure.

## Current strength

The current project is strongest as a falsification-first research lab.

Already present or partially present:

- trial preregistration;
- explicit governance gates;
- trial accounting;
- negative controls;
- data-quality adversarial event panel;
- reproducibility artifacts;
- run artifact validators;
- provider evaluation gate;
- deterministic portfolio simulation;
- capacity caps and cash starvation diagnostics;
- outlier contribution checks;
- no promotion without methodology gate.

This is not a retail trading bot architecture. It is closer to a research-control system designed to make false positives harder to accept.

## Main critique accepted

Three weaknesses are accepted as material.

### 1. Meta-overfitting of the research framework

Adding more gates can reduce naive overfitting but may create a second-order overfitting problem: strategies may be selected because they fit the validation framework rather than because they generalize.

Risk:

```text
framework design becomes the optimized object
```

Implication:

New validation machinery must itself be frozen, versioned and audited before being used to accept a strategy.

### 2. Execution realism remains insufficient

The current simulator models important constraints, but not enough execution microstructure.

Missing or insufficient:

- dynamic spread model;
- volatility-dependent slippage;
- nonlinear market impact;
- participation-rate penalty;
- order splitting;
- execution delay;
- queue position modeling;
- partial fills;
- adverse selection for passive orders.

Implication:

A strategy that survives current research checks may still fail after realistic execution-cost modeling.

### 3. Validation needs stronger finite-sample controls

Current temporal splits and OOS checks are useful but not enough to estimate the distribution of outcomes across historical regimes.

Candidate upgrades:

- purged walk-forward validation;
- embargoed temporal splits;
- combinatorial purged cross-validation for appropriate strategy families;
- DSR using explicit trial-count accounting;
- Rademacher-style anti-overfitting diagnostics for candidate families.

Implication:

Any future acceptance gate should evaluate the process distribution, not only a single OOS path.

## Upgrade tracks

The roadmap is split into four tracks. They should not be implemented all at once.

## Track A - Validation integrity

### Objective

Reduce meta-overfitting and temporal leakage risk.

### Proposed modules

```text
src/validation/purged_temporal_split.py
src/validation/embargo.py
src/validation/combinatorial_purged_cv.py
src/analysis/deflated_sharpe.py
src/analysis/rademacher_complexity.py
```

### Deliverables

- frozen validation protocol report;
- tests on synthetic time series with known leakage boundaries;
- trial accounting integration;
- output report with distributional metrics, not single-path metrics only.

### First minimal implementation

Start with purged temporal splits and embargo, not full CPCV.

Reason:

```text
Embargo/purging prevents a concrete failure mode and is easier to verify with deterministic tests.
```

## Track B - Execution realism

### Objective

Make simulator costs more conservative and path-dependent.

### Proposed modules

```text
src/execution/spread_model.py
src/execution/slippage_model.py
src/execution/market_impact.py
src/execution/order_slicing.py
src/execution/fill_model.py
```

### Cost model hierarchy

Implement in layers:

1. static cost baseline, already present;
2. dynamic spread estimate from available OHLCV proxies;
3. volatility and ADV scaled slippage;
4. square-root market impact approximation;
5. optional Almgren-Chriss schedule simulator;
6. optional queue/partial-fill model only if intraday or LOB data becomes available.

### First minimal implementation

Start with a square-root impact haircut for small-cap daily bars:

```text
impact_bps = coefficient * volatility * sqrt(order_notional / adv_notional)
```

This is not full microstructure modeling, but it is materially better than static cost for capacity-sensitive small caps.

### Required controls

- impact must be monotonic in participation rate;
- impact must be monotonic in volatility;
- zero participation implies zero impact;
- high participation must trigger rejection or severe haircut;
- all costs must be logged into trade and rejection artifacts.

## Track C - Strategy lifecycle tracking

### Objective

Represent strategies as lifecycle entities, not one-time pass/fail objects.

### Proposed lifecycle states

```text
idea
preregistered
research_running
validation_failed
validation_passed_with_caveats
paper_candidate
paper_running
degraded
killed
archived
```

### Proposed artifact

```text
vault/04-Documentazione/Research-Ledger/Strategy-Lifecycle-Ledger.md
```

### First minimal implementation

Create a ledger schema before adding any new strategy trials.

Each strategy should record:

- hypothesis;
- preregistration report;
- trial count consumed;
- validation gates used;
- data provider dependency;
- cost model version;
- current state;
- kill rules;
- promotion blockers.

## Track D - Event-driven architecture

### Objective

Create a causal architecture boundary that can eventually support both backtest and live/paper mode from the same event semantics.

### Proposed event types

```text
MarketDataEvent
SignalEvent
OrderIntentEvent
RiskDecisionEvent
ExecutionInstructionEvent
FillEvent
PortfolioStateEvent
AuditEvent
```

### Proposed modules

```text
src/events/types.py
src/events/bus.py
src/events/replay.py
src/portfolio/event_portfolio.py
src/execution/event_execution_simulator.py
```

### Non-goal for now

Do not introduce Kafka, RabbitMQ or microservices yet.

Reason:

```text
Distributed infrastructure before stable event semantics creates operational complexity without research benefit.
```

### First minimal implementation

Build an in-process deterministic event bus and replay log.

Only after the event contract is stable should external brokers be considered.

## Recommended priority order

### Priority 1 - Purged/embargoed validation split

Reason:

This directly addresses meta-overfitting and leakage risk without requiring new data.

### Priority 2 - Square-root market impact model

Reason:

This directly attacks the largest current simulator realism gap for small-cap strategies.

### Priority 3 - Strategy lifecycle ledger

Reason:

This prevents informal promotion and makes degradation/kill rules explicit.

### Priority 4 - In-process event-driven simulation skeleton

Reason:

This creates a path toward production architecture without prematurely adding microservice complexity.

## Explicit non-goals

This plan does not authorize:

- live trading;
- paper trading;
- new strategy trial;
- provider query;
- optimization sweep;
- OOS run;
- production deployment;
- Kafka/RabbitMQ migration;
- microservice rewrite.

## Proposed next research item

```text
RESEARCH-062 - Implement purged temporal split and embargo validator
```

Scope:

- TDD first;
- synthetic time-series fixtures;
- no market data download;
- no strategy trial;
- no backtest run;
- output only validation primitives and docs.

## Alternative next research item

```text
RESEARCH-063 - Specify square-root market impact model for small-cap daily bars
```

Scope:

- spec first;
- define formula, parameters and invariants;
- no integration into live strategy decisions until tested;
- no claim that it is full Almgren-Chriss or LOB simulation.

## Final verdict

The current system should be treated as:

```text
SERIOUS RESEARCH FRAMEWORK
NOT PRODUCTION EXECUTION SYSTEM
```

The next step should improve one falsification/control surface at a time, not perform a broad architecture rewrite.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
