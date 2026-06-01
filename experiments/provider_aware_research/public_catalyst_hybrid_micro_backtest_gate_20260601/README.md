# Public Catalyst Hybrid Micro-Backtest Gate 001

This gate authorizes only the design of a tiny exploratory micro-backtest using `PUBLIC-CATALYST-HYBRID-EVENT-PANEL-001`.

It does not authorize market-data download yet. The next run must use existing local daily data if available, or create a separate provider query gate before any external price request.

## Purpose

Test whether the manually audited Catalyst panel has any directional or run-up structure worth studying further.

## Non-promotable status

Even if the micro-backtest is positive, the result remains non-promotable because:

- the event panel is manually curated;
- the panel cannot prove complete historical coverage;
- the sample is tiny;
- delisted/acquired retention is not proven;
- market data joins still require their own admissibility check.

