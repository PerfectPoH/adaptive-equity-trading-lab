# Report Form 4 Cluster Buying Run 001 Parser Failure - 2026-05-23

Decision: `FORM4_CLUSTER_BUYING_ARCHIVE_CURRENT_FORM`

## Violation Status

No protocol violation occurred. The pre-run gate `PREREG-FORM4-CLUSTER-BUYING-001` was committed and pushed before the SEC query.

## Failure

`FORM4-CLUSTER-BUYING-BACKTEST-001` performed the bounded SEC query but failed to construct the event panel because one Form 4 document raised `ParseError: mismatched tag: line 34, column 2`.

## Cause

The parser treated a single malformed or wrapped SEC document as a panel-level failure.

## Reinforced Rule

Malformed individual Form 4 documents must be quarantined at document scope; they must not abort the full bounded event panel.
