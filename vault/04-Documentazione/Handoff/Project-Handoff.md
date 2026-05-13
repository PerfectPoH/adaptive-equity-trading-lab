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
