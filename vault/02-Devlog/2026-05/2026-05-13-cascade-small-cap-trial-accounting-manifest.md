---
tipo: devlog
data: 2026-05-13
agente: cascade
topic: small-cap-trial-accounting-manifest
tags: [devlog, small-cap, manifest, trial-accounting, tdd]
---

# 2026-05-13 - Small-Cap Trial Accounting Manifest

## Obiettivo

Implementare il supporto minimo al trial accounting nei manifest degli esperimenti small-cap, prima di qualunque backtest o sweep del track ranking/uscite.

## TDD

RED aggiunti:

```text
tests/test_run_manifest.py::test_build_run_manifest_keeps_trial_accounting_top_level_without_changing_config_hash
tests/test_small_cap_historical_runner.py::test_small_cap_historical_runner_writes_trial_accounting_to_run_manifest
```

Fallimenti attesi:

```text
build_run_manifest() got an unexpected keyword argument 'trial_accounting'
run_small_cap_historical_report() got an unexpected keyword argument 'trial_accounting'
```

GREEN:

```text
2 passed
27 passed
176 passed
```

## Implementazione

Moduli aggiornati:

```text
src/experiments/run_manifest.py
src/experiments/small_cap_historical_runner.py
```

Aggiunto campo top-level in `RunManifest`:

```text
trial_accounting: dict[str, Any]
```

`trial_accounting` viene passato a:

```text
build_run_manifest(..., trial_accounting=...)
run_small_cap_historical_report(..., trial_accounting=...)
```

## Invariante importante

Il trial accounting non entra nella config strategica e non cambia `config_hash`.

Motivo:

```text
config_hash = identita' della configurazione strategica/esecutiva
trial_accounting = governance/registro del tentativo
```

Quindi due run con stessa config ma trial accounting diverso mantengono lo stesso `config_hash`.

## Stato track ranking/uscite

Il track resta:

```text
PROPOSED / NOT IMPLEMENTED / NOT PROMOTED
```

Ora e' possibile registrare trial accounting nel manifest, ma non e' stato eseguito alcun nuovo esperimento ranking/exits.

## Prossimo passo consentito

Prima di qualunque backtest ranking/exits:

```text
pre-registrare TRIAL-RANKEX-001 con research question, hypothesis family, finestre, baseline e decision rule
```

Vedi [[small-cap-ranking-exits-research-track]], [[2026-05-13-cascade-small-cap-ranking-exits-track-opened]], [[Roadmap-Master]], [[backlog]].
