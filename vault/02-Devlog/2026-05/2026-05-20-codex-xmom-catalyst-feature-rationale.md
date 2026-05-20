# 2026-05-20 - XMOM catalyst feature rationale

## Contesto

Dopo la validazione strutturale della preregistration `TRIAL-XMOM-CATALYST-001`, serviva una review teorica per evitare di scegliere soglie dai winner CRMD/AEHR.

## Cosa e' stato fatto

Creati:

```text
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/feature_threshold_rationale.md
experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520/threshold_candidate_policy.csv
```

## Decisione

Le feature candidate restano:

```text
catalyst_lag
volume_persistence / volume_decay
price_digestion
```

Tutte le soglie operative restano:

```text
not_final
not_executable
TBD
```

Governance thresholds locked:

```text
minimum_accepted_trades_for_promotion = 30
top3_contribution_promotion_cap = 100%
```

## Blocco

Nessun backtest, sweep, provider query, Markov/HMM patch, paper/live o strategy promotion.

Vedi [[Report-XMOM-Catalyst-Feature-Rationale-2026-05-20]].
