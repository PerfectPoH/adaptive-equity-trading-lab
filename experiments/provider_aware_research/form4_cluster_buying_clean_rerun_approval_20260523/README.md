# Form 4 Cluster Buying Clean Rerun Approval - 2026-05-23

`FORM4-CLUSTER-BUYING-BACKTEST-001` was executed after the original pre-run gate and failed because one SEC Form 4 document raised an XML parse error. The failure was an implementation defect in document-level error isolation, not a strategy verdict.

This approval authorizes exactly one clean rerun, `FORM4-CLUSTER-BUYING-BACKTEST-002`, after adding parser recovery for embedded ownership XML and quarantine behavior for malformed individual documents.

All original thresholds, universe, data source, retention policy, and blocked actions remain unchanged.
