# Public Catalyst Hybrid Panel Expansion Gate 001

This gate defines the next valid step after `PUBLIC-CATALYST-HYBRID-MICRO-BACKTEST-001`.

The first 12-event panel produced an exploratory signal, especially in the 60d and 90d labeled diagnostics. This gate prevents the lab from turning that observation into a parameter choice.

No new event collection, provider query, web scraping, market-data download, backtest, promotion, paper trading, or live trading is authorized by this gate.

## Purpose

Expand the manually audited Catalyst panel from 12 events to a minimum of 30 and a target range of 30-50 events while preserving point-in-time proof and negative-event retention.

## Core anti-overfitting rules

- Do not choose the 60d or 90d window because the first micro-backtest liked them.
- Keep `30d`, `60d`, and `90d` as labeled diagnostics only.
- Do not optimize entry/exit dates, costs, symbols, or event types after looking at returns.
- Count discovered-but-rejected events to expose selection bias.
- Explicitly search for CRLs, delays, withdrawals, failed trials, unresolved events, delisted names, acquired names, and ticker changes.

## Promotion status

The expanded panel remains non-promotable. It may only unlock a later exploratory rerun if it passes the expansion rules.

