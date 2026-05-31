# WORKBENCH-PORTFOLIO-001 Vault Design

This vault note links the Strategy Workbench to the next planned research layer:
Portfolio Lab.

## Core Thesis

The lab should stop asking whether one isolated strategy is magical. It should
ask whether several imperfect, audited strategy components can be combined into a
more robust diagnostic portfolio.

The arithmetic remains strict:

- diversification can reduce variance and drawdown;
- it cannot turn structurally negative strategies into real edge;
- every portfolio result remains local, proxy-aware, and non-promotable until a
  real data contract and governed runner exist.

## Required Posture

- No provider query.
- No market data download.
- No paper trading.
- No live trading.
- No promotion.
- No historical weight optimization.
- No silent removal of losing strategies after seeing results.

## Planned Engine

`WORKBENCH-PORTFOLIO-001` will consume saved Workbench dry-run artifacts and
produce:

- component list;
- return matrix;
- allocation table;
- portfolio equity curve;
- drawdown series;
- correlation matrix;
- gate panel;
- final decision;
- markdown vault report.

## Main Gates

- data contract gate;
- component count gate;
- component concentration gate;
- strategy family concentration gate;
- correlation gate;
- drawdown gate;
- ex-best-component gate;
- cost stress gate;
- regime balance gate.

## Dashboard Section

The user-facing section should be called `Portfolio Lab`.

It should show:

- thesis first;
- selected components;
- allocation policy;
- portfolio curve;
- drawdown;
- contribution by strategy;
- correlation heatmap;
- ex-best survival;
- cost stress;
- plain-language verdict.

## Canonical Spec

The full design is documented in:

`docs/superpowers/specs/2026-05-31-strategy-portfolio-engine-design.md`

