---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-rankex-trial-001-validation-command
tags: [devlog, small-cap, rankex, trial-accounting, validation, tdd]
---

# 2026-05-14 - TRIAL-RANKEX-001 validation command prepared

## Obiettivo

Preparare un comando non-esecutivo e preconfigurato per una futura validation run autorizzata di `TRIAL-RANKEX-001`, senza eseguire backtest, sweep, OOS evaluation o paper trading.

## RED

Creato test:

```text
tests/test_small_cap_rankex_trial_001.py
```

Il test falliva per modulo mancante:

```text
ModuleNotFoundError: No module named 'src.experiments.small_cap_rankex_trial_001'
```

## GREEN

Creato modulo:

```text
src/experiments/small_cap_rankex_trial_001.py
```

Il modulo espone solo builder non-esecutivi:

```text
build_rankex_trial_001_validation_cli_args()
build_rankex_trial_001_validation_powershell_command()
```

Comando preparato:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli --metadata-path data/small_cap_metadata_eligible_subset30_20260511.csv --output-dir experiments/runs/small_cap_rankex_trial_001_validation_2024 --start 2024-01-02 --end 2024-12-31 --trial-id TRIAL-RANKEX-001
```

## Finestre

Solo validation window pre-registrata:

```text
2024-01-02..2024-12-31
```

Non viene preparato OOS 2025. OOS resta subordinato al validation gate.

## Verifica

```text
pytest tests/test_small_cap_rankex_trial_001.py -q -> 3 passed
pytest tests/test_small_cap_rankex_trial_001.py tests/test_small_cap_experiment_cli.py tests/test_small_cap_historical_runner.py tests/test_run_manifest.py -q -> 39 passed
pytest -q -> 183 passed
```

## Governance

Stato trial:

```text
TRIAL-RANKEX-001 VALIDATION COMMAND PREPARED / NOT RUN / NOT PROMOTED
```

Nessun esperimento storico reale e' stato eseguito in questo step.

## Prossimo passo consentito

Solo se autorizzato esplicitamente: eseguire il comando validation preconfigurato e poi valutare i gate pre-registrati. Nessuno sweep discrezionale.

Vedi [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[2026-05-14-cascade-small-cap-rankex-trial-001-accounting-wiring]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]].
