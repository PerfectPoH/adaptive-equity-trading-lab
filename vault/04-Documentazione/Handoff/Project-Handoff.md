---
tipo: handoff
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-12
tags: [handoff, progetto, agenti, small-cap]
---

# Project Handoff - Adaptive Equity Trading Lab

## Nome

Adaptive Equity Trading Lab.

## Stato in una frase

La baseline large-cap ML e' congelata come controllo negativo; il lavoro attivo e' la research track **small/mid-cap swing long-only**, ma nessuna strategia e' validata per paper trading o capitale reale.

## Principio guida

```text
Prototype != reliable strategy
Backtest != real trading
Paper trading != live trading
Live small != scaling
```

## Decisioni chiave

- Large-cap ML: pipeline tecnica riuscita, edge insufficiente, non ottimizzare ancora soglie/feature a caso.
- Small-cap swing: track principale attuale, long-only, no short, no leva, no live.
- `yfinance`: solo prototipo, non dati point-in-time.
- Ogni sweep deve avere manifest/config hash e risultare riproducibile.
- Ogni risultato positivo small-cap deve superare benchmark coerenti, outlier stress, OOS e diagnostica sizing.
- Non aggiungere nuovi filtri per riparare il 2025 senza prima rifare i run con il sizing corretto.

## Baseline Large-Cap

Run di riferimento:

```text
20260508_203628
```

Config:

```text
use_news=false
model_type=random_forest
feature_set=baseline
target=tp_before_sl
isotonic calibration
model_probability > 0.25
stop=1.5 ATR
take_profit=3 ATR
timeout=10 giorni
risk=1% per trade
```

Risultato 2024:

```text
strategy_return ~6.49%
buy_and_hold_return ~48.05%
verdict: positive_but_under_benchmark
```

Decisione: usarla come controllo negativo e memoria metodologica, non come area principale di ottimizzazione.

## Track Small-Cap Attiva

Obiettivo: trovare setup swing long-only su small/mid-cap liquide dove un trader retail possa avere un vantaggio comportamentale, con execution e risk controls piu' conservativi della baseline large-cap.

Tooling gia' implementato:

- universe builder small-cap;
- metadata builder da watchlist;
- data-quality report;
- scanner rule-based;
- market-regime guardrail;
- candidate export;
- historical runner;
- benchmark report coerenti;
- execution planner;
- portfolio backtester;
- outlier diagnostics;
- score profile;
- cash starvation diagnostics;
- setup/feature diagnostics;
- run manifest con config hash;
- regime filters configurabili;
- risk-based sizing fix nel portfolio planner.

## Ipotesi Primaria Corrente

Regole congelate piu' recenti:

```text
setup = breakout_continuation
feature_filter = open_to_close_return >= 0.10
regime_filter = iwm_close > iwm_ema_200
holding_period_bars = 5
```

Prima del fix sizing, questa ipotesi sembrava forte nel 2022-2024:

```text
return ~169.21%
pnl_excluding_top_3 positivo
ma 2022/2023 ancora negativi e P&L molto 2024-driven
```

OOS 2025 ha bloccato la promozione:

```text
H1 2025: negativo
full-year 2025 vecchio sizing: -15.91%
full-year 2025 risk-based sizing: +0.92%
```

Il fix del sizing e' promosso, la strategia no.

## Fix Critico Recente

Bug risolto:

```text
BUG-037 - Portfolio planner ignora risk_fraction
```

Vecchia logica:

```text
allocava quasi tutto il cash disponibile su un singolo trade
```

Nuova logica:

```text
risk_size = calculate_position_size(available_cash, entry_price, stop_loss, risk_fraction)
liquidity_size = floor(max_liquidity_notional / entry_price)
cash_size = floor(available_cash / entry_price)
position_size = min(risk_size, liquidity_size, cash_size)
```

Verifica riportata:

```text
pytest -> 174 passed
```

Effetto su OOS 2025:

```text
old return: -15.91%
new return: +0.92%
insufficient_funds: 18 -> 0
avg notional: 80.3k -> 8.5k
```

Ma:

```text
pnl_excluding_top_3 = -6.97k
sign_flip_excluding_top_3 = true
strategy still below ticker_holding_window and random_entry_baseline
```

## Prossimo Passo Canonico

Rerun obbligatorio:

```text
2022-2024 multi-year
setup = breakout_continuation
open_to_close_return >= 0.10
iwm_close > iwm_ema_200
risk-based sizing corretto
```

Domanda da risolvere:

```text
Il vecchio +169% era edge del segnale o era gonfiato dal sizing quasi all-in?
```

Finche' questo non e' chiaro:

```text
no paper trading
no ranking production
no nuovi filtri in-sample sul 2025
```

## Rischi Aperti Piu' Importanti

- RISK-015: small-cap backtest puo' mentire su spread, slippage e fill.
- RISK-019: survivorship bias estremo su small-cap.
- RISK-021: scanner score non monotono.
- RISK-022: outlier risk sui rendimenti small-cap.
- RISK-031/RISK-033: edge ancora 2024-driven.
- RISK-035/RISK-036: OOS 2025 non valida la strategia.
- RISK-038: OOS positivo dopo sizing ma ancora outlier-dependent.

## File Da Leggere Prima Di Lavorare

Ordine consigliato:

1. [[INDEX]]
2. [[Roadmap-Master]]
3. [[Memoria-AI]]
4. [[backlog]]
5. [[small-cap-swing-research-spec]]
6. [[2026-05-12-cascade-small-cap-risk-based-sizing-fix]]
7. [[2026-05-12-cascade-small-cap-portfolio-mechanics-audit]]
8. [[2026-05-12-cascade-small-cap-oos-2025-full-validation]]

## Comandi Base

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli
```

Nota: per i run small-cap reali controllare sempre il manifest e i parametri usati nei devlog recenti prima di rilanciare.

## Regola Finale

Il progetto non e' bloccato: e' in una fase sana di ricerca. La prossima mossa non e' "aggiungere intelligenza", ma togliere ambiguita' dal risultato con sizing corretto e confronto multi-year riproducibile.
## Latest update - Multi-year risk-sizing rerun

The 2022-2024 EMA200 gate rerun with corrected risk-based sizing reduced the old +169.21% result to +3.60%. Cash starvation is fixed, but the strategy remains below filtered benchmarks and fails ex-top3 robustness. Do not move to paper trading or production ranking. Next decision: archive this portfolio setup or open a separate ranking/exits research track with explicit trial accounting.
## Latest update - Final small-cap archive decision

The current small-cap breakout EMA200 portfolio setup is archived as not promotable. The infrastructure and risk-based sizing fix are valid, but the corrected strategy underperforms filtered benchmarks and fails ex-top3 robustness. Do not proceed to paper trading or production ranking. Any ranking/exits work must be a separate research track with explicit trial accounting.
## Latest update - Ranking/exits track opened

A separate small-cap ranking/exits research track is now open as design-only: [[small-cap-ranking-exits-research-track]]. The archived breakout EMA200 setup remains not promotable. The next step is trial accounting manifest/ledger definition, not a backtest or sweep.
## Latest update - Trial accounting manifest implemented

The small-cap runner manifest now supports top-level `trial_accounting`, separate from `config_hash`. Tests passed: targeted manifest/runner suite 27 passed and full suite 176 passed. No ranking/exits backtest has been run. Next step: pre-register `TRIAL-RANKEX-001` with windows, baselines and decision rule.
## Latest update - TRIAL-RANKEX-001 pre-registered

`TRIAL-RANKEX-001` has been pre-registered before any ranking/exits run. It authorizes only deterministic intra-candidate ranking by existing `small_cap_scanner_score` descending, with tie-breakers `relative_volume_20d`, `open_to_close_return`, and symbol order. No experiment has been run. Next step: TDD implementation of the ranking policy and trial_accounting payload wiring.
## Latest update - TRIAL-RANKEX-001 ranking policy implemented

The deterministic ranking policy for `TRIAL-RANKEX-001` is implemented with TDD: `small_cap_scanner_score` desc, `relative_volume_20d` desc, `open_to_close_return` desc, `symbol` asc. Verification passed: targeted test 1 passed, portfolio backtester suite 15 passed, full suite 177 passed. No historical experiment, sweep, OOS evaluation or paper-trading step has been run. Next allowed step: explicit `trial_accounting` payload wiring for a future authorized run.
## Latest update - TRIAL-RANKEX-001 accounting wiring ready

`TRIAL-RANKEX-001` now has canonical `trial_accounting` payload wiring via `build_rankex_trial_001_accounting()`, and experiment functions forward that payload to the runner manifest. Verification passed: targeted payload/forwarding/CLI tests 3 passed, related suite 36 passed, full suite 180 passed. No historical experiment, sweep, OOS evaluation or paper-trading step has been run. Next allowed step: prepare a validation run script/config or report template, without discretionary sweep.
## Latest update - TRIAL-RANKEX-001 validation command prepared

`TRIAL-RANKEX-001` now has a non-executing validation command builder in `src/experiments/small_cap_rankex_trial_001.py`. It prepares the pre-registered validation window only, `2024-01-02..2024-12-31`, with `--trial-id TRIAL-RANKEX-001`. Verification passed: rankex command tests 3 passed, related suite 39 passed, full suite 183 passed. No historical experiment, sweep, OOS evaluation or paper-trading step has been run. Next allowed step only if explicitly authorized: execute validation and evaluate the pre-registered gates.
## Latest update - TRIAL-RANKEX-001 validation failed

`TRIAL-RANKEX-001` validation was executed once using the preconfigured command. Result: portfolio +5.62% vs ticker_holding_window +2.54% and random +1.94%, but ex-top3 robustness failed (`pnl_excluding_top_3=-6282.54`, sign flip true). Status: `VALIDATION FAILED / STOP / NOT PROMOTED`. Do not run OOS 2025, paper trading or discretionary sweeps for this trial.
## Latest update - RankEx strategic decision

After reviewing the `TRIAL-RANKEX-001` validation failure, the simple scanner-score ranking track is closed as not promotable. Do not reuse `TRIAL-RANKEX-001`, do not open `TRIAL-RANKEX-002` as an immediate salvage attempt, and do not run OOS/paper trading/sweeps. This was later tightened by the data-quality gate decision below.
## Latest update - Small-cap data quality gate decision

Before any new small-cap trial, including cross-sectional momentum vs IWM, the project must define a Data Quality + Methodology gate. Required scope: yfinance audit on known small-cap events, universe as-of/survivorship review, random baseline bootstrap, multiple-testing ledger, and `SmallCapPortfolioBacktester` audit. Do not preregister `TRIAL-XMOM-001`, run backtests, or perform sweeps before this gate is documented.
## Latest update - Small-cap data quality audit spec

The first sub-gate is now pre-registered: [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]]. It defines independent event selection, required event categories, yfinance properties to verify, and pre-registered verdict thresholds (`usable`, `usable_with_caveats`, `not_usable`). The audit itself has not been executed. Next allowed work: compile the independent event list and execute only the data-quality audit; no strategy backtest, no XMOM preregistration, no OOS, no sweep.
## Latest update - Small-cap data quality audit result

The frozen independent-event audit was executed only for data quality. Verdict: `NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE`. `TUP` and `MULN` were not downloadable from `yfinance` in their critical event windows; `CNGL` downloaded but halt representation was only implicit/unclear with high zero-volume fraction. Do not open `TRIAL-XMOM-001` or any new small-cap trial using the current `yfinance` daily/free-data pipeline as primary evidence. Next allowed work: provider replacement / point-in-time dataset evaluation, or methodological negative control on a more reliable universe.
## Latest update - Small-cap data-quality lessons learned

A Lessons Learned report was created: [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]]. It retroactively classifies small-cap work from 2026-05-09..2026-05-14 as methodology/infrastructure stress testing, not investible edge evidence. A bounded smoke-sample check found material 2024 warrant/dilution events for `LUNR` and `BBAI`, a 2023 reverse split plus 2024 listing/warrant venue transfer for `OUST`, and no counted 2024 material event for `OPEN` in the light check. Next allowed work: scaffolding check for a fixed large-cap/ETF negative control, without strategy threshold tuning. Do not preregister or execute `TRIAL-NCTRL-001` yet.
## Latest update - NCTRL scaffolding check

`RESEARCH-046` is completed with `TECHNICAL_PASS`. Config source: `experiments/configs/nctrl_scaffolding.py`. Output dir: `experiments/runs/nctrl_scaffolding_2024_20260515`. Run ID: `run_nctrl_scaffolding_20260515`. Config hash: `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`. Manifest extras include `purpose=nctrl_scaffolding_check`; `trial_accounting` is empty. Metrics: 2500 candidate rows, 250 candidate days, 32 operational candidates, 27 days with >=1 candidate, 32 portfolio trades. This is technical scaffolding only, not strategy evidence. Next allowed step: write single-document `TRIAL-NCTRL-001` preregistration as property-based negative control; do not execute yet.
## Latest update - TRIAL-NCTRL-001 preregistration

`TRIAL-NCTRL-001` is pre-registered in [[Report-Negative-Control-Trial-001-Preregistration-2026-05-15]] as a property-based negative control, not a strategy test. Status: `PRE-REGISTERED / NOT RUN / NOT IMPLEMENTATION-COMPLETE`. Universe: AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ. Window: 2024-01-02..2024-12-31 with download warmup from 2023-01-03. Sample-size rule: closed trades < 30 => `insufficient_evidence`. Execution is blocked until TDD implementation of P5 bootstrap random baseline N=1000, P6 random-entry simulator, P4 cash ledger fixture tests, property-check report writer, and trial accounting wiring.
## Latest update - TRIAL-NCTRL-001 infrastructure complete

`RESEARCH-047` is completed as TDD infrastructure only: P4 cash-ledger fixtures, P5 bootstrap random baseline (`N=1000`, `base_seed=700`), P6 deterministic random-entry candidate simulator (`seed=701`), P7/P8 property-check report writer, and `TRIAL-NCTRL-001` trial-accounting wiring are implemented. Verification: 43 targeted tests passed. `TRIAL-NCTRL-001` has not been executed in this step; next allowed step is one preregistered execution/reporting pass, not strategy promotion.
## Latest update - TRIAL-NCTRL-001 property check result

`TRIAL-NCTRL-001` was executed once as a methodology negative-control property check. Output dir: `experiments/runs/nctrl_trial_001_2024_20260517`. Run ID: `run_nctrl_trial_001_20260517`. Config hash: `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`. Manifest period: `2024-01-02..2024-12-27`, accepted as actual last candidate/trading-day representation. Property report verdict: `PROPERTY_CHECK_PASS`; P1-P8 all pass. Portfolio had 32 trades, but this is not strategy evidence. Full report: [[Report-Negative-Control-Trial-001-Property-Check-Result-2026-05-17]]. No paper trading, no production ranking, and no small-cap trial unlock.
## Latest update - NCTRL program closed

The NCTRL program is formally closed as `CLOSED / TECHNICAL PASS`. Final status report: [[Report-Negative-Control-Program-Status-2026-05-17]]. This consolidates `RESEARCH-046` technical scaffolding, `RESEARCH-047` property-check infrastructure, and `RESEARCH-048 / TRIAL-NCTRL-001` property-check pass. The next valid work is data/provider evaluation, point-in-time/delisted/corporate-action methodology, or tooling hardening. Do not proceed to alpha sweeps, paper trading, production ranking, `TRIAL-RANKEX-002`, or `TRIAL-XMOM-001` under the current yfinance-daily small-cap data regime.
## Latest update - Small-cap data provider evaluation plan

Created [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]] as `SPEC_ONLY_NOT_EXECUTED`. It defines hard gates for point-in-time universe support, delisted symbols, corporate actions, raw/adjusted prices, halt/suspension representation, reproducibility and licensing/storage. No provider is selected, no backtest is authorized, and no small-cap trial is opened. Even a future provider pass is necessary but not sufficient: a separate methodology gate is still required before any small-cap trial.
## Latest update - Run artifact validator

Implemented `src.experiments.run_artifact_validator` as a tooling-hardening CLI. Usage: `python -m src.experiments.run_artifact_validator --run-dir <run_dir>`. It validates required run artifacts, manifest fields, CSV/JSON/markdown readability and returns exit code `0` on pass / `1` on fail. TDD coverage added in `tests/test_run_artifact_validator.py`; smoke read-only on `experiments/runs/nctrl_trial_001_2024_20260517` passed with `failed=0`. Full report: [[Report-Run-Artifact-Validator-2026-05-17]].
## Latest update - Methodology gate ledger

Created [[Report-Methodology-Gate-Ledger-2026-05-17]] as the baseline multiple-testing/methodology ledger. It records closed or blocked families, consumed degrees of freedom, required gates before any new small-cap trial, blocked trial IDs and a conservative anti-sweep policy. Status: `SPEC_ONLY / LEDGER BASELINE`; no trial opened, no backtest/OOS/sweep. Future trial-family openings, closures or material changes must update this ledger or explicitly state why no update is required.
## Latest update - Backtester audit plan

Created [[Report-Backtester-Audit-Plan-2026-05-17]] as `SPEC_ONLY_NOT_EXECUTED`. It defines a TDD audit plan for `SmallCapPortfolioBacktester` mechanics after `BUG-037`: risk-fraction sizing, cash ledger timing, entry/exit bars, costs, concurrent candidates, filters/regime gates, rejection ledger integrity and equity-curve reconciliation. No strategy trial, backtest, OOS or sweep is opened. Before any new small-cap trial, execute this audit or document why that trial does not depend on the portfolio backtester.
## Latest update - Backtester audit result

Executed the targeted TDD audit in [[Report-Backtester-Audit-Result-2026-05-17]]. RED tests showed accepted trade rows did not preserve `entry_reference_price` and planner rejection rows did not preserve diagnostics. Fixed `src/backtest/small_cap_portfolio_backtester.py` to write `entry_reference_price` to trade rows and forward planner diagnostics into rejection rows. Targeted tests passed (`28 passed`). Verdict: `TECHNICAL_PASS_WITH_LIMITATIONS`. This improves auditability only; it does not open small-cap trials.
## Latest update - Data provider event panel frozen

Created [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]] as `EVENT_PANEL_FROZEN / PROVIDER_QUERY_NOT_EXECUTED`. It freezes the mandatory seed events `TUP`, `MULN`, `CNGL`, `ABAT`, `WEYS` and five expansion slots for the future provider evaluation. No provider is selected or queried, no pricing decision is made, and no strategy trial is opened. Every future provider candidate must be tested against the same frozen panel; events cannot be replaced after provider query results are known.
## Latest update - Data provider event panel expansion filled

Created [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]] after checking public issuer/exchange sources. Expansion slots are now filled: `FSR`, `PHUN`, `GH`, `ICU`, and `DWAC -> DJT`. The proposed `CCB` July 2024 offering was rejected because retrieved public sources indicated a December 2024 offering, not July; `ICU` SeaStar Medical was substituted with verified July 10, 2024 offering evidence. Status: `EXPANSION_SLOTS_FILLED / PROVIDER_QUERY_NOT_EXECUTED`; still no provider selected, no API query, no trial.
## Latest update - Provider evaluation execution checklist

Created [[Report-Small-Cap-Provider-Evaluation-Execution-Checklist-2026-05-17]] as `CHECKLIST_READY / PROVIDER_QUERY_NOT_EXECUTED`. It turns the provider plan and frozen 10-event panel into an execution checklist with candidate provider notes, pre-execution gates, artifact layout, manifest fields, per-event audit fields, verdict rules and stop rules. Databento, Intrinio and Massive/Polygon have current public/free-trial signals; Tiingo and IEX Cloud remain direct-verification items. No provider is selected or queried, no cost is authorized, and no strategy trial is opened.
## Latest update - Provider evaluation artifact validator

Implemented `src.experiments.provider_evaluation_artifact_validator` with TDD. CLI: `python -m src.experiments.provider_evaluation_artifact_validator --evaluation-dir <provider_eval_dir>`. It validates required provider-evaluation files, `provider_manifest.json` fields, payment authorization guardrail, CSV/Markdown readability, required provider-event audit columns and exact frozen panel coverage `DPE-001..DPE-010`. Report: [[Report-Provider-Evaluation-Artifact-Validator-2026-05-17]]. This is tooling only: no provider query, no provider selected, no cost authorized, no trial opened.
## Latest update - Provider evaluation dry-run template

Created `experiments/provider_evaluations/example_provider_event_panel_20260517/` as a versioned dry-run provider-evaluation artifact template. It contains placeholder manifest, requirement table, event audit table, license notes, cost estimate, raw-response manifest, snapshot hashes and summary. The new validator passes on this template with `failed=0`, `passed=21`. Report: [[Report-Provider-Evaluation-Dry-Run-Template-2026-05-17]]. This is schema/scaffold verification only: no provider query, no provider selected, no cost authorized, no trial opened.
## Latest update - Provider evaluation runbook

Created [[Report-Provider-Evaluation-Runbook-2026-05-17]] as `RUNBOOK_READY / PROVIDER_QUERY_NOT_EXECUTED`. It defines the day-of-execution workflow for one real provider at a time: preconditions, secret handling, directory creation from the dry-run template, pre-query edits, frozen `DPE-001..DPE-010` query sequence, raw-response capture, snapshot hashing, audit row completion, validator gate, provider summary, verdict rules, stop rules, git rules and post-execution documentation. No provider is selected or queried, no cost is authorized, and no trial is opened.
## Latest update - Intrinio provider evaluation preflight

Created `experiments/provider_evaluations/intrinio_starter_event_panel_20260517/` from the dry-run template and updated Intrinio pre-query artifacts without storing or using any API key. Validator passed with `failed=0`, `passed=21`. Report: [[Report-Intrinio-Provider-Evaluation-Preflight-2026-05-17]]. An API key was pasted into chat and must be treated as exposed; rotate/replace it before any real API query. Current status: `PREFLIGHT_READY / PROVIDER_QUERY_NOT_EXECUTED`; no cost authorized, no provider response captured, no trial/backtest/OOS/sweep opened.
## Latest update - Quant research architecture upgrade plan

Created [[Report-Quant-Research-Architecture-Upgrade-Plan-2026-05-17]] from the external critique. The report accepts three material gaps: meta-overfitting risk in the validation framework, insufficient execution realism, and need for stronger finite-sample validation. It proposes a staged roadmap: purged/embargoed validation split first, square-root market impact model second, strategy lifecycle ledger third, and in-process event-driven architecture before any microservice/Kafka/RabbitMQ rewrite. Status: `SPEC_ONLY / NOT_IMPLEMENTED`; no provider query, no strategy trial, no backtest/OOS/sweep, no paper/live trading.
