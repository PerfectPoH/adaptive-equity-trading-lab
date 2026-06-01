# Portfolio Concentration Repair 001

- status: `PORTFOLIO_CONCENTRATION_REPAIR_COMPLETE`
- decision: `PORTFOLIO_CONCENTRATION_REPAIR_CANDIDATE_DIAGNOSTIC_ONLY`
- promotion_allowed: `false`
- conservative evaluations: `14`
- conservative passing repairs: `8`
- global comparison evaluations: `42`
- global passing baskets: `11`

## Search Contract

- Preserve the original three materialized components for the primary repair search.
- Add only locally testable price-based components; exclude PEAD, Form 4, PDUFA, 13D, and Catalyst data-blocked templates.
- No provider query, no market-data download, no weight optimization, no promotion.
- Repair passes only if top component contribution is <= 40%, validation net is positive, cost stress is not blocked, ex-best is not blocked, and correlation is not warned.

## Best Conservative Repair

- passes repair constraints: `true`
- policy: `primary_equal_weight`
- components: `['a42078cbf0a2ea94', '28fb7b03aa56a91e', '9474fe601e0f2bd2', 'acc065823d9dcfb7']`
- total_net_return: `385.1595325`
- validation_net_return: `214.9844045`
- max_drawdown: `-13.19355375`
- top_component_contribution: `0.36291214`

### Component Labels

- Factory Mean Reversion 180d 100bps (Mean Reversion, a42078)
- Factory Momentum 180d 100bps (Momentum, 28fb7b)
- Factory Dollar-Bar Microstructure 180d 100bps (Dollar-Bar Microstructure, 9474fe)
- My falsifiable strategy (Momentum, acc065)

## Best Global Comparison

- passes repair constraints: `true`
- policy: `primary_equal_weight`
- components: `['28fb7b03aa56a91e', 'a42078cbf0a2ea94', '9474fe601e0f2bd2']`
- total_net_return: `475.33201491`
- validation_net_return: `217.51552181`
- max_drawdown: `-14.11430053`
- top_component_contribution: `0.39208824`

### Component Labels

- Factory Momentum 180d 100bps (Momentum, 28fb7b)
- Factory Mean Reversion 180d 100bps (Mean Reversion, a42078)
- Factory Dollar-Bar Microstructure 180d 100bps (Dollar-Bar Microstructure, 9474fe)

## Final Decision Blockers

- `factory_lineage_or_proxy_data_gate`
- `same_sample_repair_search_gate`