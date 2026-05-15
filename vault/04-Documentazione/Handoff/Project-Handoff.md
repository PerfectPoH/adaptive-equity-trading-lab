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
