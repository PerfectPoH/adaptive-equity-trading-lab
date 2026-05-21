# Gap-down reversion preregistration spec

Status: `SPEC_ONLY_NOT_EXECUTED`

Preregistration id: `PREREG-GAPREV-001`

Trial id: `TRIAL-GAPREV-001`

This artifact defines a future long-only intraday gap-down reversion hypothesis.

It does not authorize data downloads, provider queries, extractor implementation, parameter sweeps, OOS execution, paper trading, live trading, or strategy promotion.

## Research Question

Can extreme overnight gap-downs that reclaim intraday VWAP before late morning produce positive post-cost intraday returns under a preregistered trend/liquidity regime?

## Scope

The trial is intentionally narrow:

- long-only;
- US equities only;
- regular trading hours only;
- intraday data required;
- no shorts;
- no averaging down;
- no overnight holding;
- no live or paper trading.

## Governance

The trial cannot become executable until a separate data contract, ingestion gate, preregistered final parameter manifest, CPCV/DSR validation path and explicit execution approval exist.
