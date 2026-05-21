---
tipo: handoff
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-20
tags: [handoff, progetto, agenti, small-cap]
---

# Project Handoff - Adaptive Equity Trading Lab

## Nome

Adaptive Equity Trading Lab.

## Stato in una frase

La baseline large-cap ML e' congelata come controllo negativo; il vecchio lavoro small-cap e' riclassificato come metodologia/infrastruttura; `TRIAL-XMOM-001` su Databento e' stato eseguito una sola volta, ha primary metric positiva, ma outlier stress fallito. Nessuna strategia e' validata per paper trading o capitale reale.

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

## Track XMOM Databento

Stato:

```text
TRIAL-XMOM-001 executed once
data provider: Databento Historical OHLCV
raw payload retention: false
status: primary metric positive, not promotable
```

Dataset:

```text
experiments/provider_aware_research/data_inputs/databento_xmom_20260520/
```

Run:

```text
experiments/runs/xmom_trial_001_20260520/
```

Gate:

```text
data ingestion gate: DATA_INPUT_VALIDATION_PASS
pre-run gate: PASS_READY_TO_EXECUTE
post-run gate: POST_RUN_VALIDATION_PASS
run artifact validator: pass
```

Risultato:

```text
total_trades: 11
return_pct: +109.36%
IWM holding-window return: +1.70%
excess_return_vs_iwm_net_of_costs: +107.66%
```

Blocco:

```text
outlier_concentration_alert: true
sign_flip_excluding_top_3: true
pnl_excluding_top_3: -50085.32
```

Decisione:

```text
primary_go_rule_passed_but_outlier_stress_blocks_promotion
```

Regole operative:

- non promuovere XMOM a paper trading;
- non fare tuning post-hoc su `TRIAL-XMOM-001`;
- non trattare il +109.36% come edge validato;
- interpretazione forense iniziale completata: top 3 winner sono AEHR 2025-09 e CRMD 2025-04/05, vicini a catalyst pubblici company-specific;
- catalyst classification completata sugli 11 trade: domanda aggiornata a `post-catalyst continuation vs post-catalyst fade`;
- preregistration spec catalyst-aware creata come `TRIAL-XMOM-CATALYST-001 / PREREG-XMOM-CATALYST-001`;
- validator strutturale della spec completato: `SPEC_VALIDATION_PASS`, 58/58;
- review teorica feature/soglie completata: catalyst lag, volume persistence/decay e price digestion;
- rationale artifacts inclusi nel validator: soglie operative restano `TBD / not_final / not_executable`;
- implementation gate spec completata: `IMPLEMENTATION_GATE_SPEC_PASS`, 47/47;
- utility DSR/PSR implementate e testate, non collegate al trial;
- utility CPCV con purging/embargo implementate e testate, non collegate al trial;
- effective trial-count estimator implementato e testato, non collegato al trial;
- synthetic statistical gate harness creato: collega DSR + CPCV + `N_eff` e rigetta il miglior trial da rumore;
- earnings-event extraction guardrails aggiunti alla implementation gate: earnings-only, reaction session BMO/AMC, purge DMT/UNSPECIFIED, min-periods rolling e bootstrap ECDF;
- provider-selection gate earnings calendar creato e validato: `EARNINGS_PROVIDER_SELECTION_GATE_PASS`, 39/39, senza query;
- prossimo lavoro ammesso: separate one-provider/one-symbol probe approval artifact, non extractor live e non esecuzione.

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
## Latest update - Intrinio one-event probe result

Created `experiments/intrinio_probe_one_event.py` and attempted a single Intrinio probe for `DPE-006 / FSR` with `payment_cap_usd=0`, no credit card attached, and no raw response retention. The endpoint returned `HTTP_ERROR_401 / Unauthorized`; recorded redacted error artifact `experiments/provider_evaluations/intrinio_starter_event_panel_20260517/DPE-006_intrinio_probe_error.json`. Report: [[Report-Intrinio-One-Event-Probe-Result-2026-05-17]]. Provider data were not evaluated; status is `INTRINIO_EVALUATION_BLOCKED_BY_AUTHENTICATION`. Verify key activation/auth method/trial endpoint before any second query.

## Latest update - Databento provider evaluation preflight

Created `experiments/provider_evaluations/databento_equities_historical_20260517/` from the dry-run template and updated Databento pre-query artifacts without storing or using any API key. User reports `125 USD` free credits, no credit card attached, and equities historical selected. Validator passed with `failed=0`, `passed=21`. Report: [[Report-Databento-Provider-Evaluation-Preflight-2026-05-17]]. A Databento API key was pasted in chat and must be treated as exposed; rotate/replace it before any real API query. Current status: `PREFLIGHT_READY / PROVIDER_QUERY_NOT_EXECUTED`; no cost observed, no provider response captured, no trial/backtest/OOS/sweep opened.

Follow-up: user authorized use of up to `125 USD` free credits. Created `experiments/databento_probe_one_event.py`, installed `databento>=0.78.0`, and attempted one micro-probe on `EQUS.MINI / trades / FSR / 2024-03-20T14:30..14:35 / limit=10` without raw retention. Databento returned `BentoClientError / 401 auth_authentication_failed`; redacted error artifact `experiments/provider_evaluations/databento_equities_historical_20260517/DPE-006_databento_probe_error.json`. Provider data not evaluated. Verify key/API access in Databento portal before any second query.

Key-source follow-up: `experiments/databento_probe_one_event.py` now supports explicit `--api-key-source auto|environment|env-file` plus redacted fingerprints. In the Codex shell, `--api-key-source env-file` resolves to `.env` fingerprint `8cecabc817e0` and still returns `BentoClientError / 401 auth_authentication_failed`; process environment key is absent. If a manual user-side metadata smoke-test passed, `.env` is not the same working key, or the script must be rerun from the working shell with `--api-key-source environment`.

Databento controlled full-panel update: created `full_panel_derived_evaluation.csv` without raw provider payload retention and updated requirement verdicts. All DPE-001..DPE-010 rows have `provider_symbol_resolves=yes`, `event_window_available=yes`, `raw_ohlcv_available=yes`. Status: `CONTROLLED_FULL_PANEL_EVALUATION_EXECUTED / DATABENTO_CAN_PROCEED_TO_NEXT_FULL_PANEL_STEP / PROVIDER_VERDICT=CAVEAT_NOT_FINAL_PASS`. Remaining caveats: adjusted OHLCV, corporate-action metadata, halt/suspension metadata, point-in-time universe support, and license/storage rights. No strategy trial/backtest/OOS/sweep/live/paper trading opened.

Databento capability diagnostics update: created `capability_diagnostics.csv`. Native `definition` schema includes `md_security_trading_status` and `security_update_action`; definition record counts returned for TUP/MULN/CNGL/WEYS/FSR/PHUN/GH/DJT. Requirement verdict now has partial_pass for corporate actions and halt/suspension representation, while point-in-time universe and licensing/storage remain caveats. Provider verdict remains `CAVEAT_NOT_FINAL_PASS`.

Databento Reference API update: docs/SDK confirm paths for adjustment factors, corporate actions, corporate-action PIT mode, and security master through `db.Reference`. Current key is not subscribed: diagnostics returned `403 license_reference_dataset_no_subscription`. Artifact `reference_api_diagnostics.csv` added. Next Databento step is enabling/subscribing to Reference datasets or asking support to confirm access/licensing; Historical OHLCV remains usable but final provider pass is blocked.

Polygon Stocks Basic Free preflight: `POLYGON_API_KEY` from `.env` used for 5 controlled calls with no raw retention and 13s pacing. Results: reference/corporate-actions useful for recent events (`MULN` split row, `WEYS` dividend rows, `DJT` ticker details, `FSR` historical ticker details); `DJT` minute aggregate returned HTTP 403. Verdict: `POLYGON_FREE_USEFUL_SECONDARY_REFERENCE_PROVIDER / NOT_FULL_OHLCV_PROVIDER_PASS`.

Databento cost decision: user reported Databento Reference API requires approximately `300 USD/month`. Decision: decline for now. Current provider combo is Databento Historical for OHLCV plus Polygon Stocks Basic Free for recent reference/corporate-actions cross-check. Final provider pass remains blocked for full PIT/reference/security-master coverage and storage rights.

Provider combo gate: Databento Historical + Polygon Stocks Basic Free is approved only for data-quality audit work, not strategy trials/backtests. Artifact `experiments/provider_evaluations/provider_combo_gate_20260518.md` and report `Report-Provider-Combo-Gate-Databento-Polygon-2026-05-18.md` define allowed next work: DPE derived feature table, event-window availability matrix, corporate-action cross-check matrix, provider join feasibility check. Blocked: backtest/OOS/sweep/live/paper/raw retention/ALL_SYMBOLS.

DPE data-quality audit layer created at `experiments/provider_evaluations/dpe_data_quality_audit_layer_20260518/`. It contains derived feature, event-window availability and corporate-action crosscheck matrices based only on prior Databento/Polygon evidence. Status: `DATA_QUALITY_AUDIT_LAYER_READY_FOR_INTERPRETATION / STRATEGY_TRIALS_REMAIN_BLOCKED`. All DPE events remain caveat; do not use for backtest/OOS/sweep/live/paper.

DPE data-quality audit interpretation complete. Verdict: `USABLE_FOR_DATA_QUALITY_AUDIT_WITH_CAVEATS / NOT_USABLE_FOR_STRATEGY_PERFORMANCE_CLAIMS / TRIALS_REMAIN_BLOCKED`. Required downstream warning policy is in `experiments/provider_evaluations/dpe_data_quality_audit_layer_20260518/downstream_warning_policy.csv`. Next allowed work: provider join feasibility, data-quality warning integration, methodology gate draft with provider caveats only.

Provider join feasibility completed. Verdict: `JOIN_FEASIBLE_FOR_DATA_QUALITY_METADATA_ONLY / NOT_FEASIBLE_FOR_PERFORMANCE_DATASET`. Artifacts in `experiments/provider_evaluations/provider_join_feasibility_20260518/`. Use only for metadata/availability/corporate-action cross-check. Do not use as a performance dataset or for adjusted returns/tradability/identifier-continuity claims.

Provider sensitivity test spec prepared at `experiments/provider_sensitivity/provider_sensitivity_test_spec_20260518/`. Status: `SPEC_ONLY_NOT_EXECUTED / READY_FOR_USER_REVIEW_BEFORE_EXECUTION`. It includes overlap selection candidates and a redacted query plan for Databento/Polygon comparison. Do not execute provider queries or backtests without explicit review/authorization.

Provider sensitivity micro-check executed. Verdict: `PROVIDER_SENSITIVITY_MICRO_CHECK_CAVEATED / STRATEGY_PROMOTION_REMAINS_BLOCKED`. Results: 4 candidates, Databento pass 3, Databento unavailable/error 1 (`CABA` 2022 coverage caveat), Polygon reference pass 4, material deltas >5% = 0 among comparable rows. Do not infer strategy validity or provider stability from this tiny sample.

Provider sensitivity coverage-aware expansion complete. Verdict: `OLD_YFINANCE_RESULTS_PROVIDER_SENSITIVE_ON_COVERAGE_AWARE_SAMPLE / STRATEGY_PROMOTION_REMAINS_BLOCKED`. In 8 Databento-covered old yfinance trade candidates, Databento passed 8/8 but 2/8 had material >5% price/return deltas. Next safe step is archive old strategy results as provider-sensitive; do not promote or paper trade.

Old signal price replay full coverage complete. Verdict: `OLD_SIGNAL_RETURNS_PROVIDER_SENSITIVE_FULL_COVERAGE_REPLAY / OLD_STRATEGY_RESULTS_NOT_SAFE_FOR_PROMOTION`. Replayed 66 old yfinance fixed signals inside Databento coverage; Databento pass 66/66, stable 25, minor delta 35, material delta 6, max_abs_return_delta ~20.85%. Next safe step: archive old strategy results as provider-sensitive; do not run portfolio backtest/paper trading from old yfinance results.

Old yfinance-era strategy results archived as provider-sensitive. Status: `OLD_YFINANCE_STRATEGY_RESULTS_ARCHIVED_AS_PROVIDER_SENSITIVE / OLD_STRATEGY_TRACK_CLOSED_NOT_PROMOTABLE`. Required warning: old yfinance-era small-cap strategy results are provider-sensitive and cannot be used as performance evidence or promotion basis. Future strategy work must restart as a provider-aware research track with explicit trial accounting.

New provider-aware research track spec created. Status: `SPEC_ONLY_NOT_EXECUTED / NEW_PROVIDER_AWARE_RESEARCH_TRACK_REQUIRED`. Future strategy research must start with provider coverage contract, adjustment policy, PIT universe policy, halt/tradability policy, trial accounting, preregistration, negative control, provider sensitivity check, and promotion policy. Recommended next step: `IMPLEMENT_PROVIDER_COVERAGE_CONTRACT_SPEC`.

Provider coverage contract spec created. Status: `SPEC_ONLY_NOT_EXECUTED / PROVIDER_COVERAGE_CONTRACT_REQUIRED_BEFORE_STRATEGY_RUN`. Required before future provider-aware strategy work: explicit coverage dates, frozen symbol scope, missingness policy, adjustment/corporate-action/halt/PIT assumptions, licensing retention policy, provider warnings, stop conditions, approved uses, and blocked uses. Recommended next step: `IMPLEMENT_PROVIDER_COVERAGE_CONTRACT_VALIDATOR`.

Provider coverage contract validator implemented. Status: `IMPLEMENT_PROVIDER_COVERAGE_CONTRACT_VALIDATOR_COMPLETE / VALIDATOR_PASS`. CLI: `python -m src.experiments.provider_coverage_contract_validator --contract-dir <dir>`. Tests: `tests/test_provider_coverage_contract_validator.py` pass 5/5. Current provider coverage contract spec passes 25/25 checks.

Adjustment/tradability policy spec and validator complete. Status: `ADJUSTMENT_TRADABILITY_POLICY_REQUIRED_BEFORE_PERFORMANCE_RESEARCH / VALIDATOR_PASS`. Current stance: diagnostics with caveats only; performance research blocked until adjustment, corporate-action, halt/tradability, PIT-universe, licensing, and provider-warning gates are satisfied. CLI: `python -m src.experiments.adjustment_tradability_policy_validator --policy-dir <dir>`.

Trial accounting and preregistration spec complete. Status: `TRIAL_ACCOUNTING_AND_PREREGISTRATION_REQUIRED_BEFORE_SIGNAL_RESEARCH / VALIDATOR_PASS`. New signal research now requires preregistered research question, hypothesis, sample, window, features, parameters, primary metric, trial budget, trial ledger, and decision threshold. CLI: `python -m src.experiments.trial_accounting_preregistration_validator --spec-dir <dir>`.

Research run gate spec and validator complete. Status: `RESEARCH_RUN_GATE_REQUIRED_BEFORE_ANY_PROVIDER_AWARE_RUN / VALIDATOR_PASS`. CLI: `python -m src.experiments.research_run_gate_validator --gate-dir <dir> --research-stage <stage>`. For `new_signal_research`, gate requires provider coverage contract, adjustment/tradability policy, and trial accounting/preregistration validators to pass.

First preregistered provider-aware research plan created. Status: `FIRST_PROVIDER_AWARE_RESEARCH_PLAN_PREREGISTERED_NOT_RUN / PLAN_VALIDATOR_PASS`. Artifact: `experiments/provider_aware_research/first_preregistered_provider_aware_research_plan_20260518`. Plan remains blocked: primary metric, feature list, parameters, sample definition, trial ledger, and gate run must be finalized before any execution. CLI: `python -m src.experiments.preregistered_research_plan_validator --plan-dir <dir>`.

First preregistered provider-aware research plan pre-run fields finalized. Status: `FIRST_PROVIDER_AWARE_RESEARCH_PLAN_PREREGISTERED_PRE_RUN_FIELDS_FINALIZED_NOT_RUN`. Primary metric: `median_next_session_open_to_close_return`; parameters: minimum_gap `0.10`, minimum_price `2.00`, minimum_dollar_volume `1000000`, market regime `IWM close > EMA200`, event window `next_session_open_to_close`, max_trials `3`. No execution performed. Next safe step: create an explicit execution authorization artifact if the user decides to permit a future run.

Explicit execution authorization spec created. Status: `EXPLICIT_EXECUTION_AUTHORIZATION_DEFINED_NOT_RUN / SPEC_ONLY_NOT_EXECUTED / AUTHORIZATION_STATUS_DEFINED_NOT_GRANTED`. Artifact: `experiments/provider_aware_research/explicit_execution_authorization_spec_20260518`. Validator: `python -m src.experiments.execution_authorization_validator --artifact-dir <dir>`. It defines one possible future controlled diagnostic execution but keeps execution blocked until explicit user approval, exact command, output artifact directory, and trial ledger entry are defined.

Execution command and output schema spec created. Status: `EXECUTION_COMMAND_AND_OUTPUT_SCHEMA_DEFINED_NOT_RUN / SPEC_ONLY_NOT_EXECUTED`. Artifact: `experiments/provider_aware_research/execution_command_output_schema_spec_20260518`. Validator: `python -m src.experiments.execution_command_output_schema_validator --artifact-dir <dir>`. Defines command id `CMD-PREREG-PA-SMALLCAP-001`, max execution count 1, required output schemas, and explicit blockers. No execution performed.

Governance calibration falsifiability spec created. Status: `GOVERNANCE_CALIBRATION_FALSIFIABILITY_DEFINED_NOT_RUN / SPEC_ONLY_NOT_EXECUTED`. Artifact: `experiments/provider_aware_research/governance_calibration_falsifiability_spec_20260518`. Validator: `python -m src.experiments.governance_calibration_validator --artifact-dir <dir>`. Direct interpretation: governance should block unsafe or uninterpretable research, not require positive performance or make all strategy designs impossible.

Dry-run preflight spec created. Status: `DRY_RUN_PREFLIGHT_DEFINED_BLOCKED_NOT_RUN / SPEC_ONLY_NOT_EXECUTED`. Artifact: `experiments/provider_aware_research/dry_run_preflight_spec_20260518`. Validator: `python -m src.experiments.dry_run_preflight_validator --artifact-dir <dir>`. Real preflight returns `blocked` with 37/37 checks passing because governance components pass but manual execution inputs remain unresolved.

Manual preflight inputs resolution spec created. Status: `MANUAL_PREFLIGHT_INPUTS_PARTIALLY_RESOLVED_RUN_NOT_APPROVED / SPEC_ONLY_NOT_EXECUTED`. Artifact: `experiments/provider_aware_research/manual_preflight_inputs_resolution_spec_20260518`. Validator: `python -m src.experiments.manual_preflight_inputs_validator --artifact-dir <dir>`. It defines a future command/module/output/ledger/credential policy but keeps execution approval not granted and no provider query performed.

Dry-run preflight updated with manual input resolution. Status: `DRY_RUN_PREFLIGHT_UPDATED_WITH_MANUAL_INPUT_RESOLUTION_BLOCKED_NOT_RUN`. Aggregate validator now includes `manual_preflight_inputs` and returns `blocked` with 38/38 checks passing. Component manual preflight inputs validates 39/39. Execution remains prohibited until explicit approval and implementation/output/ledger/credential checks are completed.

Provider sensitivity diagnostic runner dry-only implemented. Module: `src/experiments/provider_sensitivity_diagnostic_runner.py`. It requires `--dry-run`, rejects `--execute`, and rejects forbidden flags. Manual preflight inputs now mark the module as `dry_only_implemented`; aggregate preflight remains `blocked`. No provider query/backtest/sweep/run performed.

Provider sensitivity real runner gated mode implemented. `src/experiments/provider_sensitivity_diagnostic_runner.py` now supports `--real-run` only as a blocked gate report with `real_run_gates_unresolved`; it does not query providers or run backtests. Manual/dry preflight artifacts mark `real_runner_gated`; preflight remains blocked.

Provider credential preflight no-query implemented. Module: `src/experiments/provider_credential_preflight.py`. It checks env var presence only, does not disclose secrets, and performs no network/provider calls. Manual/dry preflight artifacts mark `presence_check_implemented_not_run`; aggregate preflight remains blocked. Intrinio EOD historical equities is likely appropriate if adjusted/unadjusted OHLCV plus corporate-action and coverage metadata are included.

Credential preflight local result recorded. Status: `CREDENTIAL_PREFLIGHT_LOCAL_ONLY_BLOCKED`; `DATABENTO_API_KEY` and `POLYGON_API_KEY` are missing in the current shell environment. No secrets disclosed, no provider query, no network call. Aggregate dry-run preflight remains blocked.

Pre-execution output ledger gate added. Artifact: `experiments/provider_aware_research/pre_execution_output_ledger_gate_20260518/`; validator: `src/experiments/pre_execution_output_ledger_validator.py`. It passes 29/29 and is now a seventh component in dry-run preflight. Aggregate preflight remains blocked at 39/39. No output directory, ledger entry, trial consumption, provider query, or backtest performed.

Credential preflight env-file pass recorded. `DATABENTO_API_KEY` and `POLYGON_API_KEY` are present in `.env` according to redacted presence-only inspection. No secrets disclosed, no provider query, no network call. Aggregate dry-run preflight remains blocked by explicit approval, output directory, ledger, and final command review.

Final command review spec added. Artifact: `experiments/provider_aware_research/final_command_review_spec_20260518/`; validator: `src/experiments/final_command_review_validator.py`; result: pass 29/29. Integrated as eighth dry-run preflight component. Aggregate preflight remains blocked 40/40 due to approval, gated runner, output directory, and ledger gates.

Explicit approval recorded and pre-execution artifacts prepared. Output directory `experiments/provider_aware_research/execution_outputs/RUN-PREREG-PA-SMALLCAP-001-001/` and pre-execution ledger entry were created. Trial remains not consumed and no provider query/backtest occurred. Aggregate preflight remains blocked due to `real_runner_gated`.

Approved single provider sensitivity diagnostic completed. Run `RUN-PREREG-PA-SMALLCAP-001-001`, trial `TRIAL-001`, symbol `CRMD`. Provider query performed exactly once through the approved runner path; no raw payload retained, no backtest/sweep/promotion/paper/live. Sensitivity class `provider_stable_for_selected_fields` for the selected candidate only.

Mini-panel approval gate added at `experiments/provider_aware_research/mini_panel_approval_gate_20260518/`. Status: `MINI_PANEL_DEFINED_NOT_EXECUTED / SPEC_ONLY_AWAITING_SEPARATE_APPROVAL`. It defines a 4-candidate panel with CRMD as executed anchor and 3 proposed new provider queries. Validator: `src/experiments/mini_panel_approval_gate_validator.py`, pass 36/36. No mini-panel query has been executed.

Approved mini-panel provider sensitivity diagnostic completed for `MINIPANEL-PREREG-PA-SMALLCAP-001-001` on commit `586f579`. Preflight passed 17/17. Outputs are under `experiments/provider_aware_research/execution_outputs/MINIPANEL-PREREG-PA-SMALLCAP-001-001/`. Three new provider queries were executed: IOVA 2025-07 and IOVA 2025-12 classified `minor_price_or_return_delta`; CABA classified `provider_unavailable`. Raw payload retention remained disabled and no strategy promotion/backtest/sweep/paper/live occurred.

RESEARCH-062 completed as a synthetic-only purged temporal split and embargo validator. Added `src/validation/purged_temporal_split_embargo_validator.py`, tests in `tests/test_purged_temporal_split_embargo_validator.py`, and report `experiments/validation/research_062_purged_temporal_split_embargo_report.json`. Validator passes 10/10 and targeted tests pass 8/8. No market data download, provider query, backtest, sweep or strategy promotion occurred.

RESEARCH-100 added for Intrinio EOD trial onboarding at `experiments/provider_aware_research/intrinio_eod_trial_onboarding_gate_20260518/`. Status: `SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED`. Validator: `src/experiments/intrinio_eod_trial_onboarding_validator.py`, 41/41 pass. Tests: `tests/test_intrinio_eod_trial_onboarding_validator.py`, targeted suite 16/16 pass. Critical blocker before any Intrinio query: rotate/replace the previously exposed Intrinio key, then resolve endpoint/terms/rate-limit questions and create a separate one-call probe approval gate.

Intrinio follow-up answers recorded in RESEARCH-100 gate. Status is now `SPEC_ONLY_INTRINIO_TRIAL_INFO_RESOLVED_NOT_QUERIED`; validator passes 42/42. Informational blockers resolved: small-cap support, adjusted/unadjusted availability, delisted symbols, candidate endpoints, 2000 calls/min rate limit, research validation use. Hard blockers remain before any query: rotate/replace exposed key, explicit one-call probe approval, output directory, trial ledger entry.

Intrinio credential replacement recorded for RESEARCH-100. User placed a new key in `.env` as `INTRINIO_API_KEY`; presence-only env-file preflight passed with no network call and no disclosure. Gate status: `SPEC_ONLY_INTRINIO_CREDENTIAL_READY_NOT_QUERIED`. Remaining blockers: separate one-call probe approval, output directory creation, trial ledger entry creation.

Post-run validation gate added. Validator: `src.experiments.post_run_validation_gate_validator`; spec artifact: `experiments/provider_aware_research/post_run_validation_gate_spec_20260520/`; report: [[Report-Post-Run-Validation-Gate-2026-05-20]]. The gate checks completed run artifacts for execution config presence, trade-log schema, liquidity/impact participation caps, cost consistency, summary/trade-log reconciliation and outlier diagnostics. It explicitly does not use profit as a pass condition. Local bounded replay `experiments/runs/provider_aware_oos_replay_bounded_20260520` passes `POST_RUN_VALIDATION_PASS` with `28/28` checks, meaning it is internally coherent but still not strategy-promotable because performance remains below benchmarks.

XMOM data-ingestion gate added. Validator: `src.experiments.xmom_data_input_validator`; spec artifact: `experiments/provider_aware_research/xmom_data_ingestion_gate_spec_20260520/`; report: [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]]. It requires `dataset_manifest.json`, declared file hashes, OHLCV schema, exact expected-symbol match, date-range checks, duplicate checks, positive/flexible OHLC sanity checks and configured extreme-return thresholds. The XMOM pre-run gate was hardened: `databento_data_exists` now requires `data_input_validation_report.json` with `status=pass` and `gate_decision=DATA_INPUT_VALIDATION_PASS`, not merely files in the data directory. No provider query or data ingestion has been executed.

Synthetic data-ingestion dry run completed in `experiments/provider_aware_research/xmom_data_ingestion_synthetic_dry_run_20260520/`. The synthetic dataset passes `xmom_data_input_validator` with `DATA_INPUT_VALIDATION_PASS`, `16/16`; report: [[Report-XMOM-Data-Ingestion-Synthetic-Dry-Run-2026-05-20]]. The real `TRIAL-XMOM-001` pre-run gate remains `BLOCKED_EXIT_1` because `experiments/provider_aware_research/data_inputs/databento_xmom_20260520` still lacks a real passing validation report.

Real XMOM Databento ingestion completed. Directory: `experiments/provider_aware_research/data_inputs/databento_xmom_20260520/`; report: [[Report-XMOM-Real-Data-Ingestion-2026-05-20]]. `EQUS.MINI` could not cover the preregistered 2022 start because it begins on 2023-03-28, so ingestion used venue-specific datasets: `XNAS.ITCH` for `AEHR/ARRY/CABA/CRMD/IOVA` and `ARCX.PILLAR` for `IWM`. Output contains derived `prices.csv` only, 6012 rows, 1002 per symbol, 2022-01-03 through 2025-12-30. Raw payloads were not retained. Databento degraded-day warnings were observed for some 2022 dates and recorded in `dataset_manifest.json`. Data gate passed `17/17`; XMOM pre-run gate passed `17/17` with `PASS_READY_TO_EXECUTE`. No XMOM backtest/execution has been run yet; next step requires explicit execution authorization.

XMOM earnings provider-selection gate complete. Artifact: `experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521/`; report: [[Report-XMOM-Earnings-Provider-Selection-Gate-2026-05-21]]. Validator passes `39/39`. It defines provider requirements for historical earnings-calendar coverage and report-time quality, while keeping all provider queries, extractor implementation, OOS execution, paper/live and promotion blocked.

XMOM earnings single-probe approval artifact complete. Artifact: `experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521/`; report: [[Report-XMOM-Earnings-Single-Probe-Approval-2026-05-21]]. Validator passes `38/38`; targeted tests pass `8/8`. Status remains `SPEC_ONLY_AWAITING_SEPARATE_APPROVAL`: provider and symbol are unselected, maximum scope is one provider/one symbol/one endpoint/one provider call, raw payload retention is blocked, and no provider query/extractor/OOS/paper/live/promotion has occurred.

XMOM earnings single-probe runner gate complete. Module: `src.experiments.xmom_earnings_single_probe_runner`; artifact: `experiments/provider_aware_research/xmom_earnings_single_probe_runner_gate_20260521/`; report: [[Report-XMOM-Earnings-Single-Probe-Runner-Gate-2026-05-21]]. Targeted tests pass `5/5`. `--dry-run` returns a non-executing plan; current `--real-run` returns `blocked` with exit code `2` because approval/provider/symbol/output/ledger gates are unresolved. No provider query or extractor path exists in this runner.

XMOM earnings single-probe execution preflight validator complete. Module: `src.experiments.xmom_earnings_single_probe_execution_preflight_validator`; artifact: `experiments/provider_aware_research/xmom_earnings_single_probe_execution_preflight_20260521/`; report: [[Report-XMOM-Earnings-Single-Probe-Execution-Preflight-2026-05-21]]. Targeted tests pass `6/6`. Current real preflight is intentionally blocked (`2/16` pass, `14/16` fail, exit code `1`) because explicit approval, output directory and ledger row do not exist. No provider query/extractor/OOS/paper/live/promotion occurred.

XMOM earnings single-probe explicit approval template complete. Artifact: `experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521/`; report: [[Report-XMOM-Earnings-Single-Probe-Explicit-Approval-Template-2026-05-21]]. Validator passes `30/30`; targeted tests pass `6/6`. This is only a template and approval remains `not_granted`; the live approval directory still does not exist, so execution preflight remains blocked.

XMOM earnings single-probe theoretical review complete. Artifact: `experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/`; report: [[Report-XMOM-Earnings-Single-Probe-Theoretical-Review-2026-05-21]]. Validator passes `33/33`; targeted tests pass `7/7`. The theoretical candidate is Intrinio + CRMD + `expected_earnings_dates_or_equivalent`, with `expected_8k_at` as timestamp-field candidate for BMO/AMC/DMT/UNSPECIFIED mapping. This is not approval: live approval directory, output directory and ledger remain absent; no provider query occurred.

Earnings timestamp classifier added. Module: `src.validation.earnings_timestamp_classifier`; report: [[Report-Earnings-Timestamp-Classifier-2026-05-21]]. Targeted tests pass `8/8`. It maps missing/date-only/midnight/invalid timestamps to `UNSPECIFIED/purge`, local `<09:30 America/New_York` to `BMO/same_regular_session`, `09:30..16:00` to `DMT/purge`, and `>=16:00` to `AMC/next_regular_session`. Local utility only; no provider query or extractor implementation occurred.

XMOM earnings single-probe executed after explicit approval. Artifact: `experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001/`; report: [[Report-XMOM-Earnings-Single-Probe-Execution-2026-05-21]]. Preflight passed `21/21`; one Intrinio provider call was performed for `CRMD` using `companies/{identifier}/upcoming_earnings`; result `HTTP_ERROR_403 / Forbidden`. Raw payload retention remained disabled, API key redacted, no market-data download, extractor, OOS/backtest, paper/live or promotion occurred. Interpretation: provider/access entitlement issue, not strategy evidence. The same output artifact now blocks a second execution by default.

New hypothesis-generation and video research notes archived. Report: [[Report-Quant-Hypothesis-Generation-And-Video-Research-2026-05-21]]. It captures three future hypothesis vectors: PEAD/liquidity/small-cap quality, binary biotech catalysts, and intraday gap-down reversion. It also records ideas from three videos: Renaissance-style statistical infrastructure, behavioral guardrails from trader failure modes, and microstructure/order-flow upgrades such as dollar bars, absorption and LOB filters. Status is `RESEARCH_NOTES_ARCHIVED_SPEC_ONLY`; no provider query, extractor, sweep, OOS, paper/live or promotion is authorized.

Gap-down reversion research branch opened. Artifact: `experiments/provider_aware_research/gap_down_reversion_preregistration_spec_20260521/`; report: [[Report-Gap-Down-Reversion-Preregistration-2026-05-21]]. Validator `src.experiments.gap_down_reversion_preregistration_validator` passes `43/43`; targeted tests pass `5/5`. Trial `TRIAL-GAPREV-001` is long-only, intraday-only, US equities, and blocks provider queries, intraday downloads, extractor implementation, sweeps, OOS, paper/live and promotion. Operational thresholds remain `TBD_IN_FUTURE_SPEC`, so the branch is valid but not executable.
