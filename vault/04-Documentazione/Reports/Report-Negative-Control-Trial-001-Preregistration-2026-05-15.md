---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-05-15
trial_id: TRIAL-NCTRL-001
tags: [report, negative-control, preregistration, property-based, large-cap, methodology]
---

# Report Negative Control Trial 001 Preregistration - 2026-05-15

## Stato

```text
PRE-REGISTERED / NOT RUN / NOT IMPLEMENTATION-COMPLETE
NO TRIAL EXECUTION AUTHORIZED BY THIS DOCUMENT
NO STRATEGY VALIDATION
NO EDGE INTERPRETATION
NO SMALL-CAP TRIAL UNLOCK
```

Questo documento pre-registra `TRIAL-NCTRL-001` come negative control property check della macchina di ricerca.

Non esegue il trial.
Non implementa i componenti mancanti.
Non autorizza paper trading, OOS, provider spending o nuovi trial small-cap.

## Definizione del trial

`TRIAL-NCTRL-001` verifies that the pipeline machinery satisfies pre-registered property checks when applied to a reliable-data universe. It does not test a strategic hypothesis. Pass means properties hold; fail means at least one property is violated and a latent bug or methodology issue is discovered.

In altre parole:

```text
property check, not strategy test
machine validation, not alpha validation
bug discovery surface, not promotion surface
```

## Dipendenza completata

Lo scaffolding tecnico richiesto e' completato in [[Report-Negative-Control-Scaffolding-Check-2026-05-15]].

Scaffolding result:

```text
TECHNICAL_PASS
output_dir: experiments/runs/nctrl_scaffolding_2024_20260515
run_id: run_nctrl_scaffolding_20260515
config_hash: 732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab
candidate_rows: 2500
candidate_days: 250
operational_candidates_total: 32
pct_days_with_operational_candidate: 10.8%
portfolio_total_trades: 32
trial_accounting_present: false
```

Interpretazione dello scaffolding:

```text
pipeline non muta
10 symbols/day considered
filters still active
large-cap/ETF universe accepted by universe-scope config only
```

## Universo congelato

Il trial usa lo stesso universo fixed large-cap/ETF dello scaffolding:

```text
AAPL
MSFT
NVDA
AMD
TSLA
META
AMZN
GOOGL
SPY
QQQ
```

Non sono autorizzate aggiunte, rimozioni o sostituzioni di ticker in `TRIAL-NCTRL-001`.

## Finestra temporale congelata

Validation/property-check window:

```text
2024-01-02..2024-12-31
```

Download warmup:

```text
from 2023-01-03
```

Razionale:

- le large-cap/ETF baseline sono molto piu' affidabili su `yfinance` daily rispetto alla superficie small-cap audited;
- usare la stessa finestra dello scaffolding elimina un grado di liberta';
- nessun OOS e' incluso in questo negative control;
- piu' finestre in questa fase aumenterebbero i gradi di liberta' senza migliorare il valore del property check.

## Config sorgente congelata

La config di riferimento e' committata in:

```text
experiments/configs/nctrl_scaffolding.py
```

Per `TRIAL-NCTRL-001` la config execution deve derivare da questa config, con l'aggiunta dei componenti property-check mancanti P5/P6 e del `trial_accounting` specifico del trial.

## Parametri modificabili e non modificabili

Parametri universe-scope gia' adattati e congelati:

```text
SmallCapUniverseConfig.max_market_cap = 10T
SmallCapUniverseConfig.exclude_etfs = False
SmallCapUniverseConfig.min_market_cap = 0
```

Strategy scope non modificabile:

```text
SmallCapSwingScannerConfig thresholds
SmallCapExecutionConfig gap/slippage/capacity/risk assumptions
SmallCapPortfolioBacktestConfig holding period / rank / concurrency policy
MarketRegimeGuardrailConfig thresholds
```

Non e' autorizzato ritoccare soglie per aumentare o ridurre il numero di trade.

## Trial accounting manifest payload

Quando il trial verra' eseguito, il `run_manifest.json` dovra' contenere un campo top-level `trial_accounting` equivalente a:

```json
{
  "trial_id": "TRIAL-NCTRL-001",
  "research_question": "Does the research pipeline satisfy pre-registered property checks on a fixed reliable-data large-cap/ETF control universe?",
  "hypothesis_family": "methodology_negative_control",
  "status": "pre_registered_not_run",
  "validation_window": "2024-01-02..2024-12-31",
  "download_warmup_start": "2023-01-03",
  "universe_definition": "fixed 10-symbol large-cap/ETF control universe: AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ",
  "config_source": "experiments/configs/nctrl_scaffolding.py",
  "scaffolding_run_id": "run_nctrl_scaffolding_20260515",
  "scaffolding_config_hash": "732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab",
  "decision_target": "property_checks_only",
  "sample_size_stop_rule": "if closed trades < 30 then verdict=insufficient_evidence, not passed and not failed",
  "notes_on_multiple_testing": "single negative-control property-check trial; no strategy tuning, no universe tuning, no additional windows, no benchmark pass/fail objective"
}
```

`trial_accounting` must not be part of `config_hash`; it must remain a manifest top-level accounting payload.

## Required implementation before execution

This preregistration intentionally documents all required properties before all supporting infrastructure exists.

Execution of `TRIAL-NCTRL-001` is not authorized until the following are implemented with TDD:

```text
P5 infrastructure: bootstrap random baseline distribution-aware, N=1000
P6 infrastructure: random-entry simulator preserving execution/portfolio/risk_fraction mechanics
trial accounting wiring for TRIAL-NCTRL-001
property-check report artifact writer
```

If implementation reveals a latent bug:

```text
stop
create backlog item
fix with TDD
rerun only after fix
```

No result from a suspected-bug pipeline may be interpreted.

## Property framework

The trial has eight required properties.

| ID | Property | Current implementation state | Trial requirement |
|---|---|---|---|
| P1 | pipeline end-to-end completes without error | verified by scaffolding | must pass during trial run |
| P2 | `run_manifest.json` produced and `config_hash` deterministic | verified by scaffolding and manifest tests | must pass during trial run |
| P3 | backtester respects `risk_fraction` sizing | existing BUG-037 regression path | regression test must pass before and during trial package |
| P4 | cash ledger timing coherent | requires targeted fixture tests | must pass fixture tests before execution |
| P5 | random baseline distribution-aware approximately matches buy-and-hold expectation | requires new bootstrap code | bootstrap N=1000 required before execution |
| P6 | random long-only strategy has expected ex-top3 sign-flip behavior | requires random-entry simulator | simulator required before execution |
| P7 | ex-topN arithmetic properties hold on produced trade logs | existing diagnostics partially cover | property must be auto-checked on trial output |
| P8 | benchmarks are generated and numerically sensible | indirectly verified by scaffolding | benchmark sanity checks must pass |

## Detailed property definitions

### P1 - End-to-end execution

Pass if the trial run completes without exception and writes required artifacts:

```text
candidate_export.csv
run_manifest.json
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
backtest_report.md or small_cap_backtest_report.md
property_check_report.json
property_check_report.md
```

Fail if any required artifact is missing, unreadable, empty when structurally required, or schema-incompatible.

### P2 - Manifest determinism and identity

Pass if:

```text
run_manifest.json exists
trial_accounting.trial_id = TRIAL-NCTRL-001
config_hash is deterministic for identical config
config_hash changes on config changes
universe list equals frozen baseline
period equals 2024-01-02..2024-12-31 or actual last trading day representation
```

Fail if manifest identity is missing, trial accounting is absent, or config identity is not reproducible.

### P3 - Risk-fraction sizing regression

Pass if the existing risk-fraction sizing regression tests remain green and the trial run uses:

```text
SmallCapExecutionConfig.risk_fraction = 0.01
```

Fail if portfolio sizing reverts to cash-allocation behavior, ignores `risk_fraction`, or reintroduces cash-starvation mechanics caused by BUG-037.

### P4 - Cash ledger timing

Pass if targeted fixture tests show:

```text
cash decreases on accepted entry
cash remains unavailable while position is open
cash is released on scheduled exit
same-day entry/exit ordering is deterministic
no closed-position cash is reused before intended exit timestamp
```

Fail if capital is released too early, released too late without reason, double-counted, or reused inconsistently.

### P5 - Distribution-aware random baseline

Implementation required before execution.

Pass if bootstrap random baseline with `N=1000` simulations is generated with a fixed seed policy and reports at least:

```text
mean_return
median_return
std_return
p05_return
p95_return
observations_per_simulation
comparison_to_equal_weight_or_buy_and_hold_window
```

Sanity expectation:

```text
random baseline mean should be directionally coherent with the same-period buy-and-hold/equal-weight universe return, allowing sampling noise and documented confidence interval
```

Fail if the random baseline is single-seed only, cannot reproduce, omits distribution summary, or produces numerically impossible values.

### P6 - Random-entry ex-outlier sanity

Implementation required before execution.

Pass if a random-entry long-only simulator can replace scanner-derived candidates while preserving:

```text
same universe
same date window
same execution model
same risk_fraction
same holding period
same portfolio constraints
```

The simulator must report ex-top3 sign-flip frequency across random simulations.

Sanity expectation:

```text
random strategy sign_flip_excluding_top_3 should be neither structurally always true nor structurally always false; expected frequency should be close to chance-like behavior and explicitly reported
```

Fail if random-entry simulation bypasses execution mechanics, uses different sizing, uses future data, or cannot compute ex-top3 diagnostics.

### P7 - Ex-topN arithmetic property

Pass if the property-check artifact verifies mechanical consistency of outlier diagnostics.

Required checks:

```text
portfolio_pnl_excluding_top_1 = total_pnl - top_1_positive_pnl_contribution when top trade is positive
portfolio_pnl_excluding_top_3 = total_pnl - top_3_positive_pnl_contribution when top trades are positive
if top positive trades exist, return_excluding_top_n <= portfolio_return
sign_flip flags are consistent with total and ex-topN signs
```

Fail if arithmetic does not reconcile with trade log.

### P8 - Benchmark numerical sanity

Pass if benchmark outputs are present and numerically sane:

```text
cash_flat present
IWM proxy present or explicitly unavailable with reason
equal_weight_universe present
random_entry_baseline present
ticker_holding_window present if operational candidates exist
no infinite returns
NaN only allowed with explicit zero-observation reason
observation counts coherent with candidate rows and frame availability
```

Fail if benchmark rows are missing, impossible, non-finite without reason, or inconsistent with input universe/window.

## Sample-size stop rule

Closed-trade count is not an edge criterion, but it controls interpretability of robustness properties.

Pre-declared rule:

```text
if closed_trades < 30:
  verdict = insufficient_evidence
  not passed
  not failed
  no strategy conclusion
  still report all executable properties
```

If `closed_trades >= 30`, the trial may receive `passed` or `failed` according to property checks only.

The scaffolding run produced 32 portfolio trades, so this threshold is plausible but not guaranteed for the trial implementation.

## Decision rule

Allowed verdicts:

```text
passed
failed
insufficient_evidence
blocked_missing_infrastructure
blocked_bug_found
```

### passed

All eight properties pass and `closed_trades >= 30`.

### failed

`closed_trades >= 30` and at least one implemented property fails.

### insufficient_evidence

`closed_trades < 30`, regardless of apparent return or benchmark comparison.

### blocked_missing_infrastructure

Attempted execution before P5/P6 infrastructure or required property-reporting is implemented.

### blocked_bug_found

Latent bug discovered before or during execution; stop-on-bug rule applies.

## Non-objectives

This trial does not test:

```text
whether the small-cap strategy works on large caps
whether portfolio return beats benchmark
whether scanner thresholds are good
whether large-cap universe should be traded
whether small-cap yfinance data becomes usable
```

No pass/fail criterion may reference beating `equal_weight_universe`, `SPY`, `QQQ`, random baseline, or ticker holding window as alpha evidence.

## Prohibited changes before execution

Not authorized:

- changing baseline tickers;
- changing validation window;
- adding OOS window;
- changing scanner thresholds;
- changing `risk_fraction`;
- changing holding period;
- changing regime guardrail thresholds;
- changing benchmark objective after seeing results;
- interpreting portfolio return as strategy evidence;
- using this trial to unlock small-cap trials on `yfinance` daily alone.

## Required next work before execution

1. Implement P5 bootstrap random baseline with TDD.
2. Implement P6 random-entry simulator with TDD.
3. Add P4 cash-ledger fixture tests if not already explicit enough.
4. Add property-check report writer for P1..P8.
5. Add `TRIAL-NCTRL-001` trial accounting wiring.
6. Re-run targeted tests.
7. Execute `TRIAL-NCTRL-001` once.

## Status finale

```text
TRIAL-NCTRL-001 PRE-REGISTERED
NOT RUN
NOT IMPLEMENTATION-COMPLETE
NEXT ACTION: TDD implementation for P5/P6/P4/reporting/accounting wiring
```

Vedi [[Report-Negative-Control-Scaffolding-Check-2026-05-15]], [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]], [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
