# 2026-05-20 - XMOM catalyst preregistration validator

## Contesto

Dopo la spec-only `TRIAL-XMOM-CATALYST-001`, serviva un validator strutturale per evitare che la preregistration fosse solo testo narrativo.

## Cosa e' stato fatto

Implementato:

```text
src/experiments/xmom_catalyst_preregistration_validator.py
```

Test:

```text
tests/test_xmom_catalyst_preregistration_validator.py
```

Report:

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/spec_validation_report.json
```

## Risultato

```text
SPEC_VALIDATION_PASS
passed: 58
failed: 0
```

Test mirati:

```text
5 passed
```

Aggiornamento successivo:

```text
feature_threshold_rationale.md
threshold_candidate_policy.csv
```

sono ora parte del contratto del validator. Le soglie candidate devono restare `not_final / TBD / not_executable`; solo le soglie di governance sono `final / locked`.

## Decisione

La spec e' strutturalmente valida ma resta non eseguibile.

Blocco ancora valido:

```text
no backtest
no sweep
no provider query
no paper/live
no strategy promotion
```

Vedi [[Report-XMOM-Catalyst-Preregistration-Validator-2026-05-20]].
