# Research run gate spec summary

```text
RESEARCH_RUN_GATE_REQUIRED_BEFORE_ANY_PROVIDER_AWARE_RUN
SPEC_ONLY_NOT_EXECUTED
NO_PROVIDER_QUERY
NO_BACKTEST
NO_STRATEGY_PROMOTION
```

The gate aggregates provider coverage contract, adjustment/tradability policy, and trial accounting/preregistration validators. Default decision is block unless all components required for the requested research stage pass.

Recommended next safe step: implement and run the aggregate gate validator.
