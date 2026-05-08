# Architecture

```text
Market Data
-> Data Snapshots
-> Feature Engineering
-> Scanner
-> Temporal Split
-> Label Builder
-> ML Model
-> Signal Engine
-> Optional Signal Quality Rank Filter
-> Risk Manager
-> Optional Market Exposure / Risk Fraction Adjustment
-> Execution Simulator
-> Backtest
-> Metrics
-> Experiment Log
-> Streamlit Dashboard
```

Milestone 1 keeps the runtime small. News, paper trading, Graphify, vault workflows, and institutional validation are roadmap items, not MVP code.
