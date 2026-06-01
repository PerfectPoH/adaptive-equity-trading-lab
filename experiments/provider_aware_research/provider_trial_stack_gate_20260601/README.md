# Provider Trial Stack Gate 001

This gate converts the free/trial provider map into an execution order for Portfolio Candidate 002.

The goal is not to find a single perfect data vendor. The goal is to assemble a small, auditable provider stack where each source is used only for the data class it can defend.

No provider query, market-data download, backtest, paper trading, or promotion is authorized by this gate.

## Execution order

1. Keep Norgate as the daily survivor-aware research base.
2. Keep SEC EDGAR as the free legal timestamp and filing source.
3. Use Databento credits only for a bounded intraday/dollar-bar probe, if explicitly gated before the query.
4. Treat Alpha Vantage, Nasdaq Data Link free samples, and public biotech calendars as exploratory-only unless a separate PIT admissibility gate passes.
5. Request commercial demos only after the exact missing fields are known.

## Non-negotiable rule

Each strategy sleeve must name its required data contract before any source is queried. Missing sleeves remain disabled with frozen weight. Their weight must not be redistributed into observable sleeves to manufacture a complete-portfolio result.

