# Report PEAD Earnings-Only Gate - 2026-05-21

Decision: BLOCKED_PROVIDER_EARNINGS_CALENDAR_UNAVAILABLE

## Why It Is Blocked
- Prior provider: Intrinio
- Prior endpoint: companies/{identifier}/upcoming_earnings
- Prior result: HTTP_ERROR_403 / Forbidden
- New provider query performed now: false
- Backtest performed: false

## Interpretation
PEAD earnings-only is the right next hypothesis structurally, but it cannot be executed from manual catalyst logs, daily gap proxies, or earnings dates without BMO/AMC report-time quality. The gate is therefore closed until the earnings-calendar provider access problem is resolved.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
