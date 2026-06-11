# Devlog - Provider sensitivity diagnostic runner dry only - 2026-05-18

Implemented `src/experiments/provider_sensitivity_diagnostic_runner.py` as a dry-only CLI.

```text
DRY_RUN_ONLY
NO_PROVIDER_QUERY
NO_BACKTEST
NO_STRATEGY_PROMOTION
```

The runner requires `--dry-run`, blocks `--execute`, and rejects forbidden flags such as `--all-symbols`, `--sweep`, `--promote`, `--paper`, and `--live`.

Updated manual preflight and dry-run preflight artifacts to reflect `dry_only_implemented`; execution remains blocked.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
