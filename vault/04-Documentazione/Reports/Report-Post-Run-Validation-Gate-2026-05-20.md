---
tipo: post-run-validation-gate
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: SPEC_AND_VALIDATOR_COMPLETE
---

# Report Post-Run Validation Gate - 2026-05-20

## Scope

Created a fail-closed post-run validation gate for completed research-run artifacts.

The gate is intentionally not a profitability validator. It checks whether a completed run is internally coherent before interpretation or promotion discussion.

## Validator

```text
src.experiments.post_run_validation_gate_validator
```

CLI:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.post_run_validation_gate_validator --run-dir <run_dir>
```

## Checks

- required run files exist;
- execution config contains market-impact and liquidity settings;
- trade log contains execution, cost, impact, liquidity and P&L fields;
- position notional stays within `max_liquidity_notional`;
- reconstructed participation stays below configured liquidity fraction and hard impact cap;
- impact cost is non-negative and included in estimated cost;
- long entry price is not below reference price after costs;
- portfolio summary P&L, return and trade count reconcile with the trade log;
- outlier diagnostics are present.

## Artifact

```text
experiments/provider_aware_research/post_run_validation_gate_spec_20260520/
```

## Governance Meaning

```text
PASS  -> run may be interpreted, subject to preregistered decision rules
FAIL  -> block interpretation and promotion discussion
```

Profit is not a pass condition. A losing but coherent run may pass. A profitable but incoherent run must fail.

## Status

```text
SPEC_AND_VALIDATOR_COMPLETE
NO_PROVIDER_QUERY
NO_BACKTEST
NO_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_OR_LIVE_TRADING
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
