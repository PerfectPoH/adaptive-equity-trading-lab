# Report - Provider Join Feasibility - 2026-05-18

## Status

```text
PROVIDER_JOIN_FEASIBILITY_CHECK_EXECUTED
NO_NEW_PROVIDER_QUERY
NO_RAW_PROVIDER_PAYLOAD_RETENTION
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_LIVE_TRADING
NO_PAPER_TRADING
```

## Inputs

```text
Databento Historical derived DPE evidence
Polygon Stocks Basic Free preflight evidence
DPE data-quality audit layer
Downstream warning policy
```

## Artifacts

```text
experiments/provider_evaluations/provider_join_feasibility_20260518/provider_join_feasibility_matrix.csv
experiments/provider_evaluations/provider_join_feasibility_20260518/provider_join_schema.csv
experiments/provider_evaluations/provider_join_feasibility_20260518/provider_join_feasibility_summary.md
```

## Result

```text
JOIN_FEASIBLE_FOR_DATA_QUALITY_METADATA_ONLY
NOT_FEASIBLE_FOR_PERFORMANCE_DATASET
```

## Interpretation

Databento Historical and Polygon Stocks Basic Free can be joined at the frozen DPE event level using `event_id`, `symbol` or `symbol_pair`, and `event_date`. This is sufficient for data-quality metadata, availability matrices and limited corporate-action/reference cross-checks.

It is not sufficient to construct a performance dataset because the join does not solve:

```text
adjustment factors
full point-in-time universe membership
full security-master continuity
halt/tradability feed validation
offering metadata
raw payload storage rights
```

## Allowed use

```text
provider_join_feasibility
availability audit
corporate-action crosscheck
methodology gate draft with caveats
```

## Blocked use

```text
adjusted return claims
tradability claims
full identifier-continuity claims
strategy trial
backtest
OOS
sweep
paper trading
live trading
```

## Verdict

```text
PROVIDER_JOIN_LAYER_READY_FOR_METADATA_USE
STRATEGY_DATASET_JOIN_NOT_APPROVED
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
