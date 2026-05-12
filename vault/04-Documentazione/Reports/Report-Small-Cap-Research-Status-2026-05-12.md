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
