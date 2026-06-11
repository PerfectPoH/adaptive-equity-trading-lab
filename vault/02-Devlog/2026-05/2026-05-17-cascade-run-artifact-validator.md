# 2026-05-17 - Run artifact validator

## Contesto

Dopo la chiusura NCTRL e la spec data-provider, il prossimo binario ammesso era hardening tooling, non alpha sweep.

## Cosa e' stato implementato

Aggiunto `src/experiments/run_artifact_validator.py`, eseguibile via:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.run_artifact_validator --run-dir experiments\runs\<run_dir>
```

Il validator controlla:

- presenza artifact minimi;
- manifest JSON e campi richiesti;
- CSV parseabili;
- markdown leggibili;
- property/bootstrap/random-entry JSON opzionali se presenti;
- exit code `0` su pass e `1` su fail.

## TDD

Aggiunto `tests/test_run_artifact_validator.py` con casi per run valida, file mancante, manifest invalido, CSV core vuoto, `portfolio_rejections.csv` vuoto consentito, property JSON opzionale e CLI exit code.

## Verifiche

- Test mirati: `8 passed`.
- Smoke read-only su `experiments/runs/nctrl_trial_001_2024_20260517`: `status=pass`, `failed=0`.

## Governance

Tooling hardening only. Nessun trial aperto, nessuna interpretazione strategica, nessun paper trading.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
