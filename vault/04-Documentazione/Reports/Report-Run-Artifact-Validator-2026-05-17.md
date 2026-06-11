---
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: IMPLEMENTED
scope: tooling_hardening
---

# Report Run Artifact Validator - 2026-05-17

## Status

```text
IMPLEMENTED / TESTED
TOOLING HARDENING ONLY
NO STRATEGY TRIAL OPENED
```

## Purpose

`run_artifact_validator` validates that an experiment run directory contains the minimum artifact set required for reproducible review.

It is intended for post-run artifact integrity checks, not strategy interpretation.

## Command

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.run_artifact_validator --run-dir experiments\runs\<run_dir>
```

The command prints a JSON validation report and returns:

- `0` when all checks pass;
- `1` when any check fails.

## Required artifacts

- `run_manifest.json`
- `candidate_export.csv`
- `benchmark_report.csv`
- `portfolio_trade_log.csv`
- `portfolio_equity_curve.csv`
- `portfolio_rejections.csv`
- `portfolio_summary.csv`
- `small_cap_backtest_report.md`

## Manifest fields checked

- `run_id`
- `config_hash`
- `period.start`
- `period.end`
- `universe`
- `extras`
- `trial_accounting`

## Optional artifacts checked when present

- `property_check_report.json`
- `property_check_report.md`
- `bootstrap_random_baseline.json`
- `random_entry_sign_flip_report.json`
- `backtest_report.md`

## Empty artifact policy

Most required CSV files must be parseable and non-empty.

`portfolio_rejections.csv` is allowed to be empty because a run can legitimately produce zero rejection rows. The file still must exist.

## Verification

TDD coverage added in `tests/test_run_artifact_validator.py`:

- valid minimal run directory passes;
- missing required file fails;
- invalid manifest JSON fails;
- empty core CSV fails;
- empty `portfolio_rejections.csv` passes;
- optional property report JSON is validated when present;
- CLI returns `0` on pass and `1` on fail.

Smoke check on `experiments/runs/nctrl_trial_001_2024_20260517` returned pass with zero failures.

## Governance

This tool supports research-machine hardening. It does not reopen small-cap trials, does not validate alpha and does not authorize paper trading or production ranking.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
