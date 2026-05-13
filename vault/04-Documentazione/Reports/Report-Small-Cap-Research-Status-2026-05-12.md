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
