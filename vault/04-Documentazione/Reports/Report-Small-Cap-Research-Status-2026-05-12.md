---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-05-12
tags: [report, small-cap, research-status, validation]
---

# Report Small-Cap Research Status - 2026-05-12

## Scopo

Fotografia aggiornata della research track small/mid-cap swing dopo OOS 2025, portfolio mechanics audit e fix del risk-based sizing.

## Stato sintetico

La track small-cap e' tecnicamente molto piu' matura della baseline iniziale, ma non ha ancora una strategia validata.

Verdetto operativo:

```text
Tooling promosso.
Risk-based sizing fix promosso.
Strategia non promossa.
No paper trading.
```

## Ipotesi Corrente

```text
setup = breakout_continuation
open_to_close_return >= 0.10
regime_filter = iwm_close > iwm_ema_200
holding_period_bars = 5
```

Questa ipotesi nasce da:

- ablation setup;
- feature filter ablation;
- open-to-close sensitivity;
- temporal split;
- multi-year validation 2022-2024;
- regime diagnostics;
- EMA200 gate ablation.

## Risultati Chiave

### Multi-Year 2022-2024, Prima Del Fix Sizing

```text
EMA200 gate return: ~169.21%
pnl_excluding_top_3: positivo
ma 2022 e 2023 restano negativi
P&L molto concentrato sul 2024
```

Interpretazione: ipotesi interessante, ma non ancora robusta.

### OOS H1 2025

```text
trades: 2
return: -16.09%
verdict: non validata
```

### OOS Full-Year 2025, Vecchio Sizing

```text
trades: 15
return: -15.91%
ticker_holding_window: +3.05%
random_entry_baseline: +3.92%
```

Interpretazione: il portfolio perde mentre il subset filtrato non era pessimo; quindi il problema poteva essere anche nella meccanica del portfolio.

### Portfolio Mechanics Audit

Bug trovato:

```text
SmallCapExecutionPlanner ignorava risk_fraction
```

Effetto:

```text
posizioni quasi all-in
cash quasi zero dopo molte entry
18 candidati filtrati saltati per insufficient_funds
missed trades median return: +4.63%
```

### OOS Full-Year 2025, Risk-Based Sizing

```text
trades: 30
return: +0.92%
insufficient_funds: 0
avg notional: 8.5k
pnl_excluding_top_3: -6.97k
sign_flip_excluding_top_3: true
```

Interpretazione: il fix e' corretto e migliora molto il comportamento, ma il risultato resta fragile e sotto benchmark filtrati.

## Decisioni

1. Il fix risk-based sizing e' promosso.
2. Il vecchio portfolio result pre-fix non va piu' usato come prova di edge.
3. La strategia non e' validata.
4. Non aggiungere filtri nuovi per riparare il 2025.
5. Non fare paper trading.
6. Non promuovere lo scanner score a ranking production.

## Prossimo Esperimento Canonico

Rerun:

```text
2022-2024 multi-year
breakout_continuation
open_to_close_return >= 0.10
iwm_close > iwm_ema_200
risk-based sizing corretto
```

Domanda:

```text
Il vecchio +169% sopravvive quando il portfolio non alloca quasi tutto il cash a ogni trade?
```

Interpretazione attesa:

- se crolla: il risultato precedente era path/sizing-driven;
- se regge: l'ipotesi resta interessante, ma serve comunque OOS/universe robustness;
- se migliora ma resta outlier-driven: continuare diagnostica, non paper.

## Rischi Aperti Collegati

- [[backlog#RISK-022 - Outlier risk sui rendimenti small-cap]]
- [[backlog#RISK-031 - Multi-year edge resta 2024-driven]]
- [[backlog#RISK-035 - OOS H1 2025 non valida la strategia]]
- [[backlog#RISK-036 - Portfolio OOS sottoperforma benchmark filtrato]]
- [[backlog#RISK-038 - OOS positivo dopo sizing ma outlier-dependent]]

## Devlog Di Riferimento

- [[2026-05-12-cascade-small-cap-risk-based-sizing-fix]]
- [[2026-05-12-cascade-small-cap-portfolio-mechanics-audit]]
- [[2026-05-12-cascade-small-cap-oos-2025-full-validation]]
- [[2026-05-12-cascade-small-cap-oos-2025-h1-validation]]
- [[2026-05-12-cascade-small-cap-ema200-regime-gate-ablation]]

## Nota Finale

Questo e' progresso vero: il progetto ha smesso di cercare un numero bello e sta isolando le cause del risultato. La prossima verifica deve essere chirurgica, non creativa.
## Update 2026-05-12 - Multi-year risk-sizing rerun

Il rerun 2022-2024 EMA200 con sizing corretto ha declassato il vecchio risultato +169.21% a +3.60%.

- Old sizing: 33 trade, +169,213.93 PnL, +169.21%, 8 `insufficient_funds`, avg notional 69.5k.
- Risk sizing: 41 trade, +3,601.29 PnL, +3.60%, zero `insufficient_funds`, avg notional 9.5k.
- Benchmark filtrati: ticker holding window +5.42%, random entry +4.16%.
- Ex-top3: -5,339.52, `sign_flip_excluding_top_3=true`.

Verdetto: il fix sizing e' confermato, ma il setup non e' validato come portfolio strategy. Nessun paper trading/ranking. Prossima scelta: archiviazione oppure track separato ranking/uscite con trial accounting esplicito.
## Update 2026-05-13 - Final archive decision

La track `breakout_continuation + open_to_close_return>=0.10 + IWM>EMA200` viene archiviata come portfolio strategy non promuovibile.

Motivo: dopo il fix risk-based sizing, sia OOS 2025 sia multi-year 2022-2024 restano sotto benchmark filtrati e falliscono l'ex-top3 robustness gate.

Stato operativo:

```text
ARCHIVED / NOT PROMOTED
No paper trading
No ranking production
No nuovi filtri in-sample
```

Un eventuale lavoro su ranking/uscite deve essere un nuovo track separato, con trial accounting esplicito e senza riusare il vecchio +169% come prova di edge.
## Update 2026-05-13 - Ranking/exits track opened

A new separate research track has been opened: [[small-cap-ranking-exits-research-track]].

Scope: ranking intra-candidate, exit management and portfolio construction only as a design-governed research track.

Status:

```text
PROPOSED / NOT IMPLEMENTED / NOT PROMOTED
```

Next allowed step is trial accounting manifest/ledger definition. No ranking backtest, sweep, paper trading or production promotion is authorized yet.
## Update 2026-05-13 - Trial accounting manifest implemented

`run_manifest.json` now supports top-level `trial_accounting`, passed through `build_run_manifest` and `run_small_cap_historical_report`.

Important invariant: `trial_accounting` is governance metadata and does not enter strategy config or change `config_hash`.

Verification:

```text
pytest tests/test_run_manifest.py tests/test_small_cap_historical_runner.py -q -> 27 passed
pytest -q -> 176 passed
```

Next allowed step remains pre-registration of `TRIAL-RANKEX-001`, not a ranking/exits backtest.
## Update 2026-05-13 - TRIAL-RANKEX-001 pre-registered

`TRIAL-RANKEX-001` is now pre-registered in [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]].

Scope: ranking intra-candidate only, using existing `small_cap_scanner_score` descending with pre-registered tie-breakers.

Status:

```text
PRE-REGISTERED / NOT RUN / NOT PROMOTED
```

No experiment, sweep or paper-trading step has been run. Next step is TDD implementation of the deterministic ranking policy.
## Update 2026-05-14 - TRIAL-RANKEX-001 ranking policy implemented

The deterministic ranking policy for `TRIAL-RANKEX-001` is implemented with TDD. Ordering now uses `small_cap_scanner_score` descending, then `relative_volume_20d` descending, `open_to_close_return` descending, and `symbol` ascending.

Verification:

```text
pytest tests/test_small_cap_portfolio_backtester.py::test_portfolio_backtester_uses_preregistered_rankex_tie_breakers -q -> 1 passed
pytest tests/test_small_cap_portfolio_backtester.py -q -> 15 passed
pytest -q -> 177 passed
```

Status remains:

```text
IMPLEMENTATION READY / NOT RUN / NOT PROMOTED
```

No historical experiment, sweep, OOS evaluation or paper-trading step has been run.
## Update 2026-05-14 - TRIAL-RANKEX-001 accounting wiring ready

`TRIAL-RANKEX-001` now has a canonical `trial_accounting` payload via `build_rankex_trial_001_accounting()` and experiment-level forwarding into the runner manifest.

Verification:

```text
pytest tests/test_small_cap_experiment_cli.py::test_small_cap_experiment_cli_main_passes_rankex_trial_accounting tests/test_small_cap_experiment_cli.py::test_build_rankex_trial_001_accounting_payload_matches_preregistration tests/test_small_cap_experiment_cli.py::test_run_small_cap_historical_experiment_forwards_trial_accounting -q -> 3 passed
pytest tests/test_small_cap_experiment_cli.py tests/test_small_cap_historical_runner.py tests/test_run_manifest.py -q -> 36 passed
pytest -q -> 180 passed
```

Status remains:

```text
WIRING READY / NOT RUN / NOT PROMOTED
```

No historical experiment, sweep, OOS evaluation or paper-trading step has been run.
## Update 2026-05-14 - TRIAL-RANKEX-001 validation command prepared

`TRIAL-RANKEX-001` now has a non-executing validation command builder in `src/experiments/small_cap_rankex_trial_001.py`. It prepares the pre-registered validation window only: `2024-01-02..2024-12-31`, with `--trial-id TRIAL-RANKEX-001`.

Verification:

```text
pytest tests/test_small_cap_rankex_trial_001.py -q -> 3 passed
pytest tests/test_small_cap_rankex_trial_001.py tests/test_small_cap_experiment_cli.py tests/test_small_cap_historical_runner.py tests/test_run_manifest.py -q -> 39 passed
pytest -q -> 183 passed
```

Status remains:

```text
VALIDATION COMMAND PREPARED / NOT RUN / NOT PROMOTED
```

No historical experiment, sweep, OOS evaluation or paper-trading step has been run.
## Update 2026-05-14 - TRIAL-RANKEX-001 validation failed

`TRIAL-RANKEX-001` validation was executed once using the preconfigured command. Output dir: `experiments/runs/small_cap_rankex_trial_001_validation_2024`; run_id: `run_36e6d2dc2421`; period: `2024-01-02..2024-12-27`.

Headline:

```text
portfolio_return: 5.62%
ticker_holding_window: 2.54%
random_entry_baseline: 1.94%
pnl_excluding_top_1: 1189.50
pnl_excluding_top_3: -6282.54
sign_flip_excluding_top_3: true
insufficient_funds: 0
```

Decision:

```text
VALIDATION FAILED / STOP / NOT PROMOTED
NO OOS 2025
NO PAPER TRADING
NO DISCRETIONARY SWEEP
```

See [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]].
## Update 2026-05-14 - RankEx strategic decision

Post-validation decision: close the simple `small_cap_scanner_score` ranking track. `TRIAL-RANKEX-001` remains failed/closed and must not be reused. Do not open `TRIAL-RANKEX-002` as a salvage attempt. Preferred next research direction is a separate, pre-registered cross-sectional momentum vs IWM specification, with no run before preregistration. See [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]].
## Update 2026-05-14 - Data quality gate before new small-cap trials

Post-RankEx methodology decision: before any new small-cap trial, the project must define a Data Quality + Methodology gate. Cross-sectional momentum vs IWM remains the preferred future direction, but it is blocked until yfinance/data survivorship, universe as-of construction, random baseline bootstrap, multiple-testing ledger and `SmallCapPortfolioBacktester` audit are specified. See [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]].
