# Report: Graphify Integration Gate

Date: 2026-05-23

Status: SPEC_ONLY_LOCAL_TOOLING_NOT_RUN

## Decision

Graphify is approved only as a local static-analysis helper for code and report
graph navigation. It is not approved as a data acquisition, backtest, strategy
selection, or strategy promotion mechanism.

## Scope

Approved scopes:

- `src`
- `tests`
- `vault/04-Documentazione/Reports`

Blocked paths:

- `.env`
- `.git`
- `.venv`
- `.venv-lab`
- `experiments/provider_aware_research/data_inputs`
- `experiments/provider_aware_research/execution_outputs`

Blocked actions:

- provider queries
- market data downloads
- strategy backtests
- paper trading
- live trading
- strategy promotion
- secret scanning

## Rule

The first real Graphify scan must be a separate run after this gate exists. This
report and `GRAPHIFY-INTEGRATION-001` authorize the integration wrapper and
dry-run planning only; they do not authorize a graph scan in the same step.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
