# WORKBENCH-PORTFOLIO-001 Phase Report

## Scope

Implemented the first diagnostic-only Portfolio Lab engine.

The engine composes saved Strategy Workbench dry-run artifacts and writes a local
portfolio diagnostic without provider queries, market-data downloads, paper
trading, live trading, or promotion.

## Implemented Capabilities

- Load saved Workbench components from `USER-STRATEGY-WORKBENCH`.
- Normalize component return streams from `equity_curve.csv` or `trade_list.csv`.
- Allocate through equal weight, inverse volatility, or sleeve allocation.
- Simulate weighted portfolio return, cumulative return, and drawdown.
- Emit component contribution and correlation matrix.
- Run portfolio gates:
  - data contract gate;
  - component count gate;
  - component concentration gate;
  - strategy family concentration gate;
  - correlation gate;
  - drawdown gate;
  - ex-best-component gate;
  - cost stress gate.
- Persist portfolio artifacts under `USER-STRATEGY-PORTFOLIOS`.
- Add a Streamlit `Portfolio Lab` page for component selection, allocation, chart
  inspection, gate review, and artifact persistence.

## First Local Diagnostic

Artifact directory:

`experiments/provider_aware_research/execution_outputs/USER-STRATEGY-PORTFOLIOS/e6af28bd054c120b`

Verdict:

`PORTFOLIO_ARCHIVE_COST_STRESS_FAILED`

Key metrics:

- component_count: `39`
- policy: `sleeve_allocation`
- total_net_return: `31.68414076`
- max_drawdown: `-8.6071287`
- time_underwater_ratio: `0.73397075`
- top_component_contribution: passed at `0.19886412`
- average_abs_correlation: passed at `0.05461018`
- ex_best_component_gate: passed, ex-best net return `26.96341793`
- cost_stress_gate: blocked, stressed net return `-12.26579452`

## Interpretation

The first composed portfolio is not a promoted strategy and not a real backtest.
It is an artifact-level diagnostic over saved local Workbench runs.

The result is useful because it separates two facts:

- diversification helped concentration and correlation;
- cost stress still killed the basket.

That is exactly the desired behavior. The Portfolio Lab did not turn weak or proxy
strategies into a trading system. It identified whether the ensemble improved the
shape of the evidence while keeping promotion locked.

## Governance

- `promotion_allowed`: `false`
- `paper_trading_allowed`: `false`
- `live_trading_allowed`: `false`
- `provider_query_performed`: `false`
- `market_data_download_performed`: `false`
- `portfolio_backtest_performed`: `false`

