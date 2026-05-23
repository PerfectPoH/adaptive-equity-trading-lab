# GRAPHIFY-INTEGRATION-001

Status: SPEC_ONLY_LOCAL_TOOLING_NOT_RUN

This artifact approves a local-only integration path for the Graphify code graph
tool without executing a repository scan in the same step.

Graphify may be used only to inspect local code/document structure and produce
queryable graph artifacts. It is not approved for provider queries, market data
downloads, strategy backtests, paper trading, live trading, or strategy
promotion.

Source repository: https://github.com/safishamsi/graphify

Observed package metadata during inspection:

- PyPI package: graphifyy
- CLI command: graphify
- Inspected version: 0.8.16

Any first real Graphify scan must be a separate run with its own output
directory and must preserve the blocked paths and blocked actions in this
artifact.
