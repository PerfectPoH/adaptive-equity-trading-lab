# 2026-05-20 - XMOM Trial 001 execution

## Contesto

L'utente ha autorizzato esplicitamente l'esecuzione della prima run reale `TRIAL-XMOM-001` dopo il passaggio del data-ingestion gate e del pre-run gate Databento.

## Cosa e' stato fatto

Implementato un runner singolo:

```text
src/experiments/xmom_trial_runner.py
```

Aggiunto test minimo:

```text
tests/test_xmom_trial_runner.py
```

Eseguita una sola run preregistrata:

```text
experiments/runs/xmom_trial_001_20260520/
```

Non sono stati eseguiti sweep, tuning discrezionale, paper trading o live trading.

## Gate

```text
pre-run gate: PASS_READY_TO_EXECUTE
post-run gate: POST_RUN_VALIDATION_PASS
run artifact validator: pass
```

## Risultato

```text
total_trades: 11
return_pct: +109.36%
IWM holding-window return: +1.70%
excess_return_vs_iwm_net_of_costs: +107.66%
```

## Diagnostica critica

```text
outlier_concentration_alert: true
top_1_pnl_contribution_pct: 60.95%
top_3_pnl_contribution_pct: 145.80%
pnl_excluding_top_3: -50085.32
sign_flip_excluding_top_3: true
```

## Decisione

Verdetto:

```text
primary_go_rule_passed_but_outlier_stress_blocks_promotion
```

Il risultato e' positivo come metrica primaria ma non robusto. La strategia non viene promossa.

Blocco ancora valido:

```text
no paper trading
no live trading
no strategy promotion
no tuning post-hoc su TRIAL-XMOM-001
```

## Test

Eseguiti:

```text
pytest tests/test_xmom_trial_runner.py
post_run_validation_gate_validator
run_artifact_validator
```

Vedi [[Report-XMOM-Trial-001-Execution-2026-05-20]], [[Project-Handoff]].
