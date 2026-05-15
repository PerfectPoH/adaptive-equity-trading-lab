---
tipo: lessons-learned
progetto: adaptive-equity-trading-lab
data: 2026-05-15
tags: [lessons-learned, small-cap, data-quality, yfinance, survivor-bias, governance]
---

# Report Small-Cap Lessons Learned - Data Quality - 2026-05-15

## Stato

```text
LESSONS LEARNED ONLY
NO NEW TRIAL OPENED
NO STRATEGY BACKTEST
NO VALIDATION
NO OOS
NO SWEEP
TRIAL-XMOM-001 NOT AUTHORIZED
TRIAL-NCTRL-001 NOT YET PREREGISTERED
```

Questo documento cristallizza la conseguenza retroattiva del verdict in [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]].

## Lesson 1 - Il risultato dell'audit e' informativamente positivo

Il data-quality audit ha falsificato l'ipotesi operativa che `yfinance` daily fosse utilizzabile come dataset primario per nuovi trial small-cap.

Questo e' un esito negativo per l'uso immediato del dataset, ma positivo per la governance: il problema e' stato scoperto prima di pre-registrare `TRIAL-XMOM-001`, prima di aprire un nuovo trial e prima di produrre nuovi risultati strategici su base dati non informativa.

Il fallimento critico su `TUP` non rappresenta solo missing noise. Rappresenta il caso peggiore per una strategia long-only small-cap: un evento distressed/delisting puo' sparire dalla superficie scaricabile, riducendo artificialmente il rischio di coda osservabile.

## Lesson 2 - Riclassificazione retroattiva del lavoro small-cap 2026-05-09..2026-05-14

Alla luce dell'audit, i risultati small-cap prodotti dal 2026-05-09 al 2026-05-14 non devono piu' essere letti come misure robuste di edge investibile.

Devono essere letti come:

```text
stress test metodologici e infrastrutturali
non evidenza primaria di edge small-cap
non base per paper trading
non base per promotion
non base per nuovi trial small-cap con yfinance daily alone
```

Questa riclassificazione include, non esaustivamente:

- setup disentangler;
- breakout-only ablation;
- open-to-close sensitivity;
- temporal split validation;
- EMA200 regime diagnostics;
- multi-year rerun;
- OOS 2025;
- `TRIAL-RANKEX-001`.

I numeri storici come `+169.21%` old sizing, `+3.60%` corrected multi-year, `+0.92%` OOS 2025 e `+5.62%` RankEx validation restano utili per capire bug, outlier dependence, cash starvation, ranking fragility e reportistica. Non devono essere citati come segnale direzionale su small-cap senza una fonte dati point-in-time con delisted symbols e corporate actions affidabili.

## Ex-post smoke sample check

Questo e' un check leggero, non un secondo audit pre-registrato.

Obiettivo: quantificare se gia' nella smoke watchlist del 2026-05-10 esistevano corporate-action/dilution/listing issues che la pipeline trattava come semplice OHLCV daily.

Smoke 2 tickers effettivamente usati:

```text
BBAI
LUNR
OPEN
OUST
```

`BLDE` era nella watchlist iniziale, ma escluso per metadata incompleto e quindi non contato qui.

### Risultato conservativo

| Ticker | 2024 material event found in light check | Event type | Source basis | Interpretation |
|---|---|---|---|---|
| LUNR | yes | warrant exercise / new warrants / dilution | issuer press release, 2024-01-11 | 2024 smoke included a ticker with material financing/warrant event during the tested year |
| BBAI | yes | warrant exercise agreements / new warrants / dilution | issuer-hosted S-3, recent developments, Feb-Mar 2024 | 2024 smoke included a ticker with material financing/warrant events during the tested year |
| OPEN | no counted event | none confirmed in light check | issuer/SEC search surfaced 2025 actions and 2024 shelf context, not a counted 2024 price-impact event | do not infer absence; only no counted event from this bounded check |
| OUST | yes, but mostly pre-window/structure | 2023 reverse split; 2024 listing/warrant exchange transfer | issuer press releases, 2023-04-20 and 2024-12-10 | 2024 OHLCV sits after a major split-adjustment history and includes listing/warrant venue changes |

Conservative count:

```text
2024 material financing/dilution events counted: 2 / 4 tickers
2024 listing/warrant venue event counted: 1 / 4 tickers
pre-2024 reverse split history affecting adjusted series: 1 / 4 tickers
no counted material event in light check: 1 / 4 tickers
```

This is not a causal correction to smoke returns. It is a governance warning: even the early successful smoke sample was not a clean, ordinary OHLCV universe. At least half of the effective smoke tickers had material 2024 financing/warrant events, and one had recent reverse-split-adjusted history.

## Consequence for old smoke interpretation

The 2026-05-10 smoke 2 result remains useful as an end-to-end pipeline proof:

```text
CLI -> metadata -> download -> feature prep -> scanner -> guardrail -> execution proxy -> report
```

It should not be used as evidence that the small-cap setup had edge.

The previous smoke verdict `beats_primary_benchmark` is therefore reclassified as:

```text
pipeline smoke success
not strategy evidence
not edge evidence
not promotion evidence
```

## Governance rule for future negative control preregistration

The next methodological work may be `TRIAL-NCTRL-001`, but only as a property-based negative control on a more reliable universe.

Before execution, the preregistration must explicitly freeze scaffolding rules:

```text
modifiable only for universe scope:
  SmallCapUniverseConfig.max_market_cap -> up
  SmallCapUniverseConfig.exclude_etfs -> False if SPY/QQQ are included
  SmallCapUniverseConfig.min_market_cap -> down only if needed for fixed control universe consistency

not modifiable for strategy scope:
  SmallCapSwingScannerConfig thresholds
  SmallCapExecutionConfig gap/slippage/capacity assumptions
  SmallCapPortfolioBacktestConfig holding period / sizing / concurrency policy
  regime guardrail thresholds
```

The negative control must be framed as a property-based test of the research machine, not as a strategy trial seeking edge.

Minimum required properties for the preregistration:

```text
P1: pipeline end-to-end completes without error
P2: run_manifest.json is produced and config_hash is deterministic
P3: backtester respects risk_fraction sizing regression from BUG-037
P4: cash ledger releases capital with coherent timing
P5: random baseline is distribution-aware, not a single seed
P6: random long-only ex-outlier behavior is sanity checked
P7: portfolio_return_excluding_top_3 is mechanically <= portfolio_return when top trades are profitable
P8: benchmarks are generated and numerically sensible
```

Sample-size stop rule must be predeclared:

```text
if closed trades < 30: verdict = insufficient_evidence
not passed
not failed
no strategy conclusion
```

## Decision

Do not proceed directly to provider spending or `TRIAL-XMOM-001`.

Current recommended order:

1. Lessons Learned documented here.
2. Technical scaffolding check for fixed large-cap/ETF control universe, without tuning strategy thresholds.
3. Single-document preregistration for `TRIAL-NCTRL-001` as property-based negative control.
4. Execute `TRIAL-NCTRL-001` once, only after preregistration.
5. Consider small-cap provider replacement only if the research machine passes the negative control.

Vedi [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]], [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]], [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[2026-05-10-cascade-small-cap-smoke-runs]], [[2026-05-10-cascade-small-cap-portfolio-diagnostics-report]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
