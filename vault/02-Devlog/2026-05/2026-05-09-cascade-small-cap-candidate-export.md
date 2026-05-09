---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-candidate-export
tags: [devlog, small-cap, scanner, execution, export, tdd]
---

# 2026-05-09 - Small-Cap Candidate Export

## Contesto

Dopo universe builder, data-quality report, market-regime guardrail, scanner ed execution planner, mancava un punto di integrazione che producesse una tabella giornaliera di candidati small-cap operativi e diagnostici.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_candidate_export.py`.
- Modulo `src/experiments/small_cap_candidate_export.py`.
- Config `SmallCapCandidateExportConfig`.
- Funzione `build_small_cap_candidate_export`.
- Funzione `write_small_cap_candidate_export`.

## Pipeline logica

Per ogni simbolo candidato:

```text
candidate metadata
-> universe builder
-> data-quality report
-> small-cap swing scanner
-> market-regime guardrail
-> conservative execution planner
-> operational_candidate
```

## Output principali

```text
as_of
symbol
operational_candidate
passes_universe_filter
universe_rejection_reasons
data_quality_status
data_quality_warnings
data_quality_errors
small_cap_setup
small_cap_scanner_score
small_cap_scanner_pass
small_cap_scanner_reject_reason
market_regime_trade_allowed
market_regime_block_reason
small_cap_execution_valid
small_cap_execution_skip_reason
small_cap_entry_reference_price
small_cap_entry_price
small_cap_position_size
small_cap_position_notional
small_cap_max_liquidity_notional
avg_dollar_volume_20d
```

## Modalita'

Default:

```text
operational_only=True
```

Restituisce solo righe operative. Con `operational_only=False`, include anche righe diagnostiche per simboli rigettati o mancanti.

## Nota su as_of

Quando `as_of` e' storico, l'export mantiene una barra successiva se disponibile per permettere all'execution planner di stimare il next-open plan. La riga candidata rimane quella del giorno `as_of`.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_candidate_export.py
4 passed
```

## Prossima mossa

Definire benchmark small-cap coerenti e poi costruire un backtest dedicato che usi gli output diagnostici senza contaminare la baseline large-cap congelata.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-execution]], [[Roadmap-Master]].
