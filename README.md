# Adaptive Equity Trading Lab

Research infrastructure for falsifiable equity-strategy experiments.

This repository is **not** a trading bot and does **not** contain a promoted
live strategy. It is a personal quantitative research lab built to answer a
harder question:

> Can a strategy idea survive data-quality checks, transaction costs,
> out-of-sample validation, robustness gates, audit trails, and provider
> constraints without turning into a false positive?

Current operating mode: `RISK_REGIME_ENGINE_ONLY`. No paper trading, no live
trading, no capital deployment.

## Why This Exists

Most backtests fail quietly. They look good because of survivorship bias,
look-ahead leakage, tiny samples, unpriced transaction costs, duplicated
signals, outlier dependence, or repeated parameter searches.

This lab is designed to make those failures visible.

It turns each research idea into a governed experiment:

```text
idea -> preregistered contract -> data gate -> backtest/probe
     -> robustness gates -> decision ledger -> vault report
```

The most important result so far is not a profitable strategy. It is a system
that repeatedly refused to promote weak evidence.

## Current State

| Area | Status |
| --- | --- |
| Strategy promotion | `0 promoted` |
| Live/paper trading | Disabled |
| Primary posture | `RISK_REGIME_ENGINE_ONLY` |
| Active hypothesis | Regime-router component membership |
| Frozen protocol | Monthly OOS companion replication |
| Main blocker | Admissible point-in-time / delisted data for stronger claims |

The active hypothesis is not "market timing works". The audit decomposed the
router into:

- **Membership**: which components are allowed for each regime.
- **Timing**: switching between regime baskets at the right moment.

Membership remains under observation. Timing is suggestive but not
statistically confirmed.

See:

- [Current state](vault/00-Progetto/Stato-Corrente.md)
- [Membership criterion](vault/01-Feature/Criterio-Preregistrato-Membership-2026-06.md)
- [Honest baselines report](vault/04-Documentazione/Reports/Report-Honest-Baselines-Trial-2026-06-11.md)
- [TRUE-ETF family closure](vault/04-Documentazione/Reports/Report-True-ETF-Family-Closure-2026-06-11.md)

## What The Lab Does

### Governance and audit

- Pre-run gates before provider queries or backtests.
- Decision ledgers for every yes/no research outcome.
- Obsidian-style vault for reports, devlogs, blockers, and state snapshots.
- Protocol freezing for future replication.
- Trial-count accounting for multiplicity-aware validation.

### Data admissibility

- Explicit provider gates.
- Point-in-time and survivorship-bias checks.
- Raw/derived retention rules.
- Delisted/stale-symbol handling.
- Quarantine logic so failed downloads are not treated as delistings.

### Backtesting and diagnostics

- Cost realism gates.
- Outlier-dependency checks.
- Median and win-rate gates.
- Deflated Sharpe Ratio and multiplicity budgets.
- OOS splits and preregistered companion baselines.
- Regime-aware portfolio diagnostics.
- Streamlit Portfolio Studio for inspecting strategy components.

### Research memory

The repository keeps a permanent audit trail in `vault/`. Failed hypotheses are
first-class artifacts, not deleted experiments.

Examples of archived or blocked research branches include:

- small-cap momentum,
- gap-down RTH reversion,
- SEC 8-K event timing and Tape Oracle variants,
- PEAD blocked by unavailable point-in-time earnings data,
- Form 4 cluster buying data-starvation,
- Kronos-based risk filtering,
- TRUE-ETF variants on free data.

## Important Results

### Studio OOS protocol

A preregistered regime-component rule passed internal OOS gates on historical
proxy streams, then was frozen for monthly replication.

Important caveat: proxy-stream performance is not a capital-deployable claim.
It is a candidate hypothesis that must survive future data.

### Honest baseline audit

The headline regime-routing edge was decomposed into honest baselines:

- cost-matched static baseline,
- unconditional top-5 component selection,
- regime-membership blend,
- regime-timing permutation test.

The audit found that component **membership** is the real hypothesis worth
tracking; timing alone was not significant.

### TRUE-ETF true backtest

The TRUE-ETF family was tested on real capital-aware data and closed after
three configurations. None passed the full gate stack on free data.

This is recorded as a successful falsification, not a failure of the
infrastructure.

## Project Layout

```text
dashboard/
  app.py                  legacy audit console
  studio.py               Portfolio Studio UI

src/
  experiments/            probes, trials, diagnostics, runners
  risk/                   regime classifier and risk overlays
  validation/             DSR, multiplicity and robustness helpers

experiments/
  runs/                   generated trial artifacts
  provider_aware_research/execution_outputs/
                          provider-gated research outputs
  replica_ledger/         persistent monthly-replication ledger

vault/
  00-Progetto/            current state and project memory
  01-Feature/             preregistrations and feature specs
  02-Devlog/              development logs
  03-Bug/                 methodological risk backlog
  04-Documentazione/      reports and indexes
```

## Run Locally

Create a Python environment, install dependencies, then run tests or the
dashboard.

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\streamlit.exe run dashboard/studio.py
```

The legacy audit console is still available:

```powershell
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

Some experiments require local data files or provider credentials. The lab is
designed to block provider use until a pre-run gate has been written and
approved.

## What This Repository Is Good For

This is a portfolio case study in:

- reproducible ML/research infrastructure,
- financial-data quality control,
- backtesting governance,
- statistical validation,
- experiment accounting,
- Streamlit research tooling,
- turning negative results into auditable evidence.

It is intentionally conservative. A strategy that cannot survive the gates is
archived instead of promoted.

## What This Repository Is Not

- Not financial advice.
- Not a trading signal service.
- Not a live-trading system.
- Not a claim of profitable alpha.
- Not an institutional-grade dataset.

The repository demonstrates engineering discipline around quantitative
research. The current research conclusion is that stronger claims require an
admissible data bundle with point-in-time and delisted coverage.
