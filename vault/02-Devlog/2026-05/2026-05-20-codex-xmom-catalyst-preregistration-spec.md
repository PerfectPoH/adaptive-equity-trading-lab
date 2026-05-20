# 2026-05-20 - XMOM catalyst preregistration spec

## Contesto

Dopo la classificazione manuale catalyst degli 11 trade XMOM, la domanda di ricerca si e' spostata da momentum generico a:

```text
post-catalyst continuation vs post-catalyst fade
```

## Cosa e' stato fatto

Creata spec-only preregistration:

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/
```

Artifact:

```text
README.md
hypothesis.md
catalyst_taxonomy.csv
allowed_features.csv
parameter_freeze.csv
decision_rule.csv
blocked_actions.csv
source_hierarchy.csv
```

Aggiornato ledger con:

```text
TRIAL-XMOM-CATALYST-001
PREREG-XMOM-CATALYST-001
prepared_not_executed
pending_spec_review
```

## Decisione

La spec congela l'ipotesi, ma non autorizza esecuzione.

Bloccati:

```text
no backtest
no sweep
no Markov/HMM patch
no paper/live
no strategy promotion
```

## Prossimo lavoro ammesso

Validator strutturale della spec o review manuale. Non esecuzione.

Vedi [[Report-XMOM-Catalyst-Trial-001-Preregistration-Spec-2026-05-20]].
