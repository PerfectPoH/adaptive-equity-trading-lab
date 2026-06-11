# 2026-05-17 - NCTRL property-check infrastructure

## Contesto

`TRIAL-NCTRL-001` era pre-registrato come property-based negative control, con stato `PRE-REGISTERED / NOT RUN / NOT IMPLEMENTATION-COMPLETE`. L'esecuzione del trial restava bloccata finche' non fossero disponibili P4/P5/P6/P7/P8 e accounting wiring.

## Cosa e' cambiato

- Aggiunte fixture P4 su `SmallCapPortfolioBacktester` per cash ledger timing: cash locked fino a exit, release prima dei candidati successivi, rejection senza consumo cash, missing holding path, equity curve con posizioni aperte.
- Implementato P5: `SmallCapBootstrapRandomBaselineConfig` e `build_bootstrap_random_baseline_report` con `simulations=1000`, `base_seed=700`, seed range `[700, 1699]` e statistiche distributive.
- Implementato P6: `NctrlRandomEntrySimulatorConfig` e `build_nctrl_random_entry_candidate_export`, che produce candidate export random deterministico compatibile con il portfolio backtester preservando execution/portfolio mechanics.
- Implementato P7/P8: `NctrlPropertyCheckResult`, `build_nctrl_property_check_report` e writer markdown con tabella `Property | Status | Evidence | Notes`.
- Aggiunto accounting wiring `build_nctrl_trial_001_accounting()` e mapping CLI `--trial-id TRIAL-NCTRL-001`.

## Verifiche

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests/test_small_cap_portfolio_backtester.py tests/test_small_cap_benchmarks.py tests/test_nctrl_random_entry_simulator.py tests/test_nctrl_property_report.py tests/test_small_cap_experiment_cli.py
```

Risultato: `43 passed`.

## Decisione

`RESEARCH-047` e' completato come infrastruttura TDD. `TRIAL-NCTRL-001` non e' stato eseguito in questo step. Prossimo passo ammesso: preparare/eseguire una singola run del trial secondo preregistrazione, usando il nuovo accounting e report writer, senza interpretazione strategica anticipata.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
