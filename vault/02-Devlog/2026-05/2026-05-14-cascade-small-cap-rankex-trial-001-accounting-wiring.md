---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-rankex-trial-001-accounting-wiring
tags: [devlog, small-cap, rankex, trial-accounting, tdd]
---

# 2026-05-14 - TRIAL-RANKEX-001 accounting wiring

## Obiettivo

Rendere esplicito e riusabile il payload `trial_accounting` pre-registrato per una futura run autorizzata di `TRIAL-RANKEX-001`, senza eseguire backtest, sweep o paper trading.

## RED

Aggiunti test:

```text
tests/test_small_cap_experiment_cli.py::test_build_rankex_trial_001_accounting_payload_matches_preregistration
tests/test_small_cap_experiment_cli.py::test_run_small_cap_historical_experiment_forwards_trial_accounting
```

Il primo test falliva per modulo mancante:

```text
ModuleNotFoundError: No module named 'src.experiments.small_cap_trial_accounting'
```

## GREEN

Creato modulo:

```text
src/experiments/small_cap_trial_accounting.py
```

Funzione canonica:

```text
build_rankex_trial_001_accounting()
```

La funzione restituisce il payload pre-registrato con:

```text
trial_id = TRIAL-RANKEX-001
status = implementation_ready_not_run
ranking_policy = small_cap_scanner_score desc, relative_volume_20d desc, open_to_close_return desc, symbol asc
candidate_run_id = None
```

Aggiornato `run_small_cap_historical_experiment` e `run_small_cap_watchlist_experiment` per accettare e inoltrare `trial_accounting` al runner, che lo scrive nel `run_manifest.json`.

## Verifica

```text
pytest tests/test_small_cap_experiment_cli.py::test_small_cap_experiment_cli_main_passes_rankex_trial_accounting tests/test_small_cap_experiment_cli.py::test_build_rankex_trial_001_accounting_payload_matches_preregistration tests/test_small_cap_experiment_cli.py::test_run_small_cap_historical_experiment_forwards_trial_accounting -q -> 3 passed
pytest tests/test_small_cap_experiment_cli.py tests/test_small_cap_historical_runner.py tests/test_run_manifest.py -q -> 36 passed
pytest -q -> 180 passed
```

## Governance

Stato trial:

```text
TRIAL-RANKEX-001 WIRING READY / NOT RUN / NOT PROMOTED
```

Non sono stati eseguiti esperimenti storici reali, sweep, OOS evaluation o paper trading.

## Prossimo passo consentito

Preparare una run script/config esplicita per validation window solo se autorizzata, usando il payload canonico, oppure preparare un report template. Nessuno sweep discrezionale e nessuna promozione.

Vedi [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[2026-05-14-cascade-small-cap-rankex-trial-001-ranking-policy]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]].
