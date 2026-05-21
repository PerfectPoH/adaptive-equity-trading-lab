---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-05-21
agente: codex
tags: [xmom, earnings, provider, probe, runner, gate, no-query]
---

# 2026-05-21 - XMOM Earnings Single Probe Runner Gate

## Contesto

After the single-probe approval artifact, the next safe implementation step was to add a runner/preflight layer that cannot query a provider unless the separate approval and all pre-execution inputs are resolved.

## Cosa e' cambiato

Added:

```text
src/experiments/xmom_earnings_single_probe_runner.py
tests/test_xmom_earnings_single_probe_runner.py
experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/
```

The runner supports:

```text
--dry-run
--real-run
```

Current `--real-run` returns a blocked report and exit code `2`.

## Verifiche

Targeted tests:

```text
5 passed
```

Saved reports:

```text
single_probe_runner_dry_run_plan.json
single_probe_runner_real_run_block_report.json
real_run_exit_code.txt
```

## Decisione

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion occurred.

The runner is a safety layer only. The probe remains blocked until explicit separate approval selects provider, symbol, endpoint, immutable output directory and ledger entry.

See [[Report-XMOM-Earnings-Single-Probe-Runner-Gate-2026-05-21]].
