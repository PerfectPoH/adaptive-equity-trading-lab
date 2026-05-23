# Report: Graphify Source Scan Smoke Test

Date: 2026-05-23

Run id: GRAPHIFY-SRC-RUN-20260523

Gate: GRAPHIFY-INTEGRATION-001

Status: GRAPHIFY_LOCAL_SRC_SCAN_COMPLETE

## Scope

The scan was limited to the approved `src` scope. No provider query, market data
download, strategy backtest, paper trading, live trading, or strategy promotion
was performed.

## Execution

Installed package observed: `graphifyy 0.4.23`

Entrypoint used:

```text
py -3 -m graphify update <repo>/src
```

Graphify 0.4.23 writes `graphify-out` beside the target path. The generated
output was moved from `src/graphify-out` to the bounded run directory:

```text
experiments/tooling/graphify_runs/graphify_src_20260523/graphify-out
```

Intermediate cache files were not retained.

## Output

Generated files:

- `graph.json`
- `GRAPH_REPORT.md`
- `graph.html`

Graph stats:

- Files scanned: 138
- Nodes: 1484
- Edges: 3498
- Communities: 65

## Smoke Query

Question:

```text
Where is the Deflated Sharpe Ratio implemented?
```

The query returned the expected source area, including:

- `src/validation/deflated_sharpe.py`
- `deflated_sharpe_ratio()`
- `return_moments()`

## Decision

Graphify is operational as a local repository navigation helper. This run is not
strategy evidence and does not authorize data acquisition, backtesting, or
promotion decisions.
