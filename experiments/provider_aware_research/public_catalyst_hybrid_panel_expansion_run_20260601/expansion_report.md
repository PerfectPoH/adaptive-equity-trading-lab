# PUBLIC-CATALYST-HYBRID-PANEL-EXPANSION-RUN-001

## Verdict

`PUBLIC_CATALYST_HYBRID_PANEL_EXPANSION_PASS_EXPLORATORY_ONLY`

The manual public-catalyst panel expansion passed the exploratory data-contract gate. This is not a strategy promotion and not a live-trading claim.

## Counts

- Total panel rows: 34
- Admissible events: 33
- Exploratory-only rows: 1
- Attrition log rows: 10
- Non-success or unresolved admissible events: 22
- Non-success or unresolved share: 66.67%
- Mapping complication count: 6
- Future event count as of 2026-06-01: 10

## Governance

- Provider query performed: false
- Market data join performed: false
- Backtest performed in this run: false
- Promotion allowed: false

## Interpretation

The expansion solves the immediate small-sample problem from the original 12-event panel, but it does not solve the complete historical-coverage problem. The panel is still manually assembled from public sources and therefore remains exploratory.

The future rows are allowed only as event-panel inventory. They must be excluded from any completed historical backtest until the event date and return window have matured.

## Next Gate

A separate micro-backtest rerun gate is required before joining this expanded panel to local daily prices. The rerun must keep the existing 30/60/90 day windows fixed and labeled as diagnostics, not optimized parameters.

