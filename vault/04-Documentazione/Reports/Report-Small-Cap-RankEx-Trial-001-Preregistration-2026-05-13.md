---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-05-13
trial_id: TRIAL-RANKEX-001
tags: [report, small-cap, ranking-exits, preregistration, trial-accounting]
---

# Report Small-Cap RankEx Trial 001 Preregistration - 2026-05-13

## Stato

```text
PRE-REGISTERED / NOT RUN / NOT PROMOTED
```

Questo documento pre-registra `TRIAL-RANKEX-001` prima di qualunque backtest, sweep o implementazione ranking/exits.

## Contesto

Track padre:

```text
small-cap-ranking-exits-research-track
```

Setup archiviato di riferimento:

```text
breakout_continuation
open_to_close_return >= 0.10
IWM close > EMA200
holding_period_bars = 5
risk_fraction = 0.01
```

Stato setup archiviato:

```text
ARCHIVED / NOT PROMOTED
```

Il setup archiviato non puo' essere usato come prova promozionale. Serve solo come baseline tecnica corretta.

## Trial accounting manifest payload

Payload da usare nel campo top-level `trial_accounting` del `run_manifest.json` quando verra' eseguito un esperimento associato:

```json
{
  "trial_id": "TRIAL-RANKEX-001",
  "research_question": "ranking_intra_candidate",
  "hypothesis_family": "ranking",
  "status": "pre_registered_not_run",
  "train_or_design_window": "2022-01-03..2023-12-29",
  "validation_window": "2024-01-02..2024-12-31",
  "oos_window": "2025-01-02..2025-12-29",
  "universe_definition": "same eligible 30-name small-cap metadata subset used by corrected archived validation unless explicitly superseded by a new pre-registered universe file",
  "baseline_run_id": "small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_risk_sizing_20260512",
  "candidate_run_id": null,
  "benchmark_set": [
    "cash_flat",
    "iwm_proxy",
    "equal_weight_universe",
    "random_entry_baseline",
    "ticker_holding_window",
    "archived_setup_corrected_risk_sizing"
  ],
  "ex_top_n_results_required": [1, 3],
  "decision_rule": "candidate may only advance if validation beats ticker_holding_window and random_entry_baseline, remains positive excluding top1 and top3 trades, shows no single-year/regime dependency, keeps insufficient_funds near zero without increasing risk_fraction, and then passes the pre-declared 2025 OOS window",
  "notes_on_multiple_testing": "first ranking/exits trial after archive decision; no parameter sweep or additional ranking family is authorized by this preregistration"
}
```

## Research question

```text
Quando piu' candidati filtrati competono nello stesso giorno, esiste un ranking intra-candidate semplice e pre-registrato che preserva o migliora il valore lordo senza introdurre overfitting?
```

## Hypothesis family

```text
ranking
```

Non sono inclusi in questo trial:

```text
exit management
portfolio construction
sector/theme caps
correlation clustering
nuovi filtri di segnale
```

Questi richiedono trial separati.

## Ranking candidate family autorizzata

Il trial autorizza solo una famiglia semplice:

```text
rank by existing small_cap_scanner_score, descending
```

Tie-breaker pre-registrati:

```text
1. higher relative_volume_20d
2. higher open_to_close_return
3. alphabetical symbol order for deterministic final tie
```

Non e' autorizzato introdurre nuove feature ranking in questo trial.

## Finestre temporali

### Design window

```text
2022-01-03..2023-12-29
```

Uso consentito:

```text
verificare implementazione, sanity check e schema output
```

Non uso consentito:

```text
scegliere soglie dopo aver visto performance aggregate
```

### Validation window

```text
2024-01-02..2024-12-31
```

Uso:

```text
prima valutazione decisionale del ranking candidate
```

### OOS window

```text
2025-01-02..2025-12-29
```

Uso:

```text
solo se il validation gate e' superato
```

## Baseline obbligatorie

Ogni report del trial deve includere:

```text
cash_flat
IWM proxy
equal_weight_universe
random_entry_baseline
ticker_holding_window
archived_setup_corrected_risk_sizing
```

## Metriche obbligatorie

- Portfolio return.
- Total P&L.
- Trade count.
- Win rate.
- Median trade return.
- P&L excluding top 1.
- P&L excluding top 3.
- Sign flip excluding top 1/top 3.
- Top 3 contribution ratio.
- Rejection summary.
- `insufficient_funds` count.
- Average notional.
- Minimum cash after entry.
- Annual breakdown.
- Benchmark comparison.

## Decision rule

Il trial puo' avanzare da validation a OOS solo se tutte le condizioni sono vere:

1. validation portfolio return batte `ticker_holding_window`;
2. validation portfolio return batte `random_entry_baseline`;
3. `pnl_excluding_top_1` resta positivo;
4. `pnl_excluding_top_3` resta positivo;
5. nessun sign flip ex-top1/ex-top3;
6. il risultato non dipende da un solo anno/regime;
7. `insufficient_funds` resta vicino a zero;
8. `risk_fraction` resta `0.01`.

Il trial puo' essere considerato promotable solo dopo OOS 2025 se anche OOS supera gli stessi gate.

## Stop rule

Stop immediato se una delle condizioni seguenti avviene in validation:

```text
underperform ticker_holding_window
underperform random_entry_baseline
pnl_excluding_top_3 <= 0
sign_flip_excluding_top_3 = true
insufficient_funds reappears as material bottleneck
```

## Cosa NON e' autorizzato

- Nessun paper trading.
- Nessun ranking production.
- Nessun nuovo filtro in-sample.
- Nessun tuning di `risk_fraction`.
- Nessun cambio di holding period.
- Nessun exit management in questo trial.
- Nessun sector cap/correlation cap in questo trial.
- Nessuna seconda ranking formula senza nuovo trial ID.

## Stato operativo finale

```text
TRIAL-RANKEX-001 pre-registered.
No experiment run.
No strategy promoted.
Next action may be TDD implementation of deterministic ranking policy and manifest payload wiring for a future run.
```

Vedi [[small-cap-ranking-exits-research-track]], [[2026-05-13-cascade-small-cap-trial-accounting-manifest]], [[Roadmap-Master]], [[backlog]].
## Implementation update 2026-05-14

The pre-registered deterministic ranking policy has been implemented with TDD in `src/backtest/small_cap_portfolio_backtester.py`.

Ordering:

```text
small_cap_scanner_score desc
relative_volume_20d desc
open_to_close_return desc
symbol asc
```

Status remains `IMPLEMENTATION READY / NOT RUN / NOT PROMOTED`. No experiment, sweep, OOS evaluation or paper-trading step has been run.
## Accounting wiring update 2026-05-14

The canonical `trial_accounting` payload for `TRIAL-RANKEX-001` is implemented in `src/experiments/small_cap_trial_accounting.py` as `build_rankex_trial_001_accounting()`. `run_small_cap_historical_experiment` and `run_small_cap_watchlist_experiment` now accept `trial_accounting` and forward it to the runner manifest.

Status remains `WIRING READY / NOT RUN / NOT PROMOTED`. No experiment, sweep, OOS evaluation or paper-trading step has been run.
