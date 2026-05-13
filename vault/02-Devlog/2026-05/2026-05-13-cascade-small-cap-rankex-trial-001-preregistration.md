---
tipo: devlog
data: 2026-05-13
agente: cascade
topic: small-cap-rankex-trial-001-preregistration
tags: [devlog, small-cap, rankex, preregistration, trial-accounting]
---

# 2026-05-13 - Small-Cap RankEx Trial 001 Preregistration

## Obiettivo

Pre-registrare `TRIAL-RANKEX-001` prima di qualunque backtest o sweep ranking/exits.

## Output

Creato report:

```text
vault/04-Documentazione/Reports/Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13.md
```

Stato:

```text
PRE-REGISTERED / NOT RUN / NOT PROMOTED
```

## Scope autorizzato

Solo ranking intra-candidate:

```text
rank by existing small_cap_scanner_score, descending
```

Tie-breaker:

```text
1. higher relative_volume_20d
2. higher open_to_close_return
3. alphabetical symbol order
```

## Scope escluso

```text
exit management
portfolio construction
sector/theme caps
correlation clustering
nuovi filtri di segnale
risk_fraction tuning
holding period tuning
```

## Finestre

```text
design: 2022-01-03..2023-12-29
validation: 2024-01-02..2024-12-31
OOS: 2025-01-02..2025-12-29
```

## Decision rule

Per avanzare a OOS il trial deve battere `ticker_holding_window` e `random_entry_baseline`, restare positivo ex-top1/ex-top3, non avere sign flip, non dipendere da un solo regime/anno e mantenere `risk_fraction=0.01` con `insufficient_funds` vicino a zero.

## Stato operativo

Nessun esperimento eseguito.

Prossimo passo consentito:

```text
TDD implementazione ranking policy deterministica + wiring del payload trial_accounting per una futura run
```

Vedi [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[small-cap-ranking-exits-research-track]], [[2026-05-13-cascade-small-cap-trial-accounting-manifest]], [[Roadmap-Master]], [[backlog]].
