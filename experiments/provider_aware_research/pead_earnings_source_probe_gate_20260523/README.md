# PROBE-PEAD-EARNINGS-SOURCE-001

Status: APPROVED_PRE_QUERY_NOT_EXECUTED

This gate authorizes one bounded earnings-source probe for PEAD data
requirements. It is not a strategy trial and cannot backtest or promote.

Provider candidate: Intrinio

Symbol: CRMD

Endpoint: `companies/{identifier}/upcoming_earnings`

The probe must determine whether the source exposes enough point-in-time fields
to calculate SUE without leakage: earnings date, BMO/AMC timestamp or equivalent,
actual EPS, consensus EPS, and timestamp/revision metadata.
