---
tipo: devlog
data: 2026-05-11
agente: cascade
topic: small-cap-wide-smoke-diagnostics
tags: [devlog, small-cap, portfolio, smoke, diagnostics, outlier-risk, score-profile, manifest]
---

# 2026-05-11 - Small-Cap Wide Smoke Diagnostics

## Contesto

Dopo run manifest ed ex-outlier stress test, il gate successivo era ripetere la smoke su una watchlist realmente piu' ampia e compatibile con i filtri small-cap.

La prima wide smoke con 9 simboli non aveva ampliato il trade set operativo: molte aggiunte erano large-cap rispetto al filtro `max_market_cap=5B`, oppure venivano escluse dal prezzo minimo. Quindi e' stata costruita una lista piu' small-cap-oriented.

## Metadata e universo

Metadata generati da provider:

```text
data/small_cap_metadata_eligible_watchlist_20260511.csv
```

Diagnostica metadata:

```text
BLDE: missing_market_cap
LAZR: missing_market_cap
VLD: missing_market_cap
```

Filtro manuale applicato prima della run:

```text
100M <= market_cap <= 5B
```

Subset finale usato dalla run robusta:

```text
data/small_cap_metadata_eligible_subset30_20260511.csv
```

Output:

```text
experiments/runs/small_cap_smoke_eligible_subset30_fast_20260511
```

Run manifest:

```text
run_id: small_cap_subset30_fast_20260511
config_hash: fca81fbd8d026236c4cdd4a4cd6883d8d18d3613a07e5548b8037131af4ef696
period: 2024-01-02 -> 2024-12-27
universe_count: 30
```

Universe:

```text
AEHR, AMPX, ARRY, ATEC, BBAI, CABA, CERS, CRCT, CRMD, DLO,
EOSE, EVGO, GCT, GDRX, GERN, IOVA, KURA, LAC, LUNR, MVST,
NVTS, OUST, PACB, PRCH, QS, ROOT, SANA, SHLS, SLDP, ZYME
```

Tutti i 30 ticker del subset sono stati scaricati correttamente con downloader one-off a timeout esplicito.

## Candidati operativi

La run ha prodotto piu' diversificazione rispetto alla smoke iniziale.

```text
OUST: 13
BBAI: 12
LAC: 11
AMPX: 11
EVGO: 10
CRMD: 10
SLDP: 10
MVST: 9
NVTS: 9
GCT: 8
EOSE: 7
SHLS: 7
LUNR: 7
ATEC: 7
ARRY: 6
AEHR: 6
CABA: 6
DLO: 6
QS: 5
ZYME: 5
GDRX: 5
KURA: 5
PRCH: 3
GERN: 2
IOVA: 2
CERS: 0
CRCT: 0
PACB: 0
ROOT: 0
SANA: 0
```

Portfolio rejections:

```text
insufficient_funds: 142
```

## Benchmark comparison

```text
cash_flat: 0.000000
iwm_proxy: -0.022805
equal_weight_universe: 0.010365
random_entry_baseline: 0.008448
ticker_holding_window: 0.025437
portfolio_return: -0.221614
```

Il portfolio perde contro cash, equal-weight universe, random baseline e ticker holding window.

## Portfolio summary

```text
initial_cash: 100000.0
ending_cash: 77838.585984
total_pnl: -22161.414016
return_pct: -0.221614
total_trades: 40
total_rejections: 142
```

## Outlier ed ex-outlier

```text
total_pnl: -22161.414016
gross_profit: 94041.507192
gross_loss: -116202.921209
top_1_pnl_contribution_pct: -1.143592
top_3_pnl_contribution_pct: -2.290198
top_5_pnl_contribution_pct: -3.109640
top_10_pnl_contribution_pct: -3.841993
outlier_concentration_alert: False
pnl_excluding_top_1: -47505.027490
portfolio_return_excluding_top_1: -0.475050
sign_flip_excluding_top_1: False
pnl_excluding_top_3: -72915.431661
portfolio_return_excluding_top_3: -0.729154
sign_flip_excluding_top_3: False
pnl_excluding_top_5: -91075.428998
portfolio_return_excluding_top_5: -0.910754
sign_flip_excluding_top_5: False
best_trade_symbol: GERN
best_trade_pnl: 25343.613474
worst_trade_symbol: CABA
worst_trade_pnl: -33146.475370
```

Interpretazione: il problema qui non e' un risultato positivo drogato dai top winner; il portfolio e' gia' negativo prima di rimuovere gli outlier.

## Score profile

```text
Q1 score 80.0: trades=18, avg_return=0.000211, median_return=0.040279, win_rate=0.6111, total_pnl=-25231.644317
Q2 score 83.3333: trades=14, avg_return=0.042132, median_return=0.003340, win_rate=0.5000, total_pnl=12354.328360
Q3 score 100.0: trades=8, avg_return=-0.039585, median_return=-0.043308, win_rate=0.2500, total_pnl=-9284.098059
```

Verdetto score:

```text
FAIL: lo score non e' monotono.
```

Il bucket massimo (`100`) e' peggiore del bucket intermedio e perde denaro. Questo conferma che `small_cap_scanner_score` non puo' essere usato per sizing, filtri live o priorita' di capitale.

## P&L per simbolo

Top positivo:

```text
GERN: +25343.61
LUNR: +17835.72
EOSE: +9220.67
NVTS: +8953.61
ARRY: +5150.18
```

Peggiori contributori:

```text
CABA: -32131.88
GDRX: -17408.19
BBAI: -12113.64
DLO: -9021.75
OUST: -8440.98
QS: -7142.56
AMPX: -5007.59
CRMD: -3772.92
```

## Verdetto finale

```text
NON PROMUOVERE.
```

Motivi:

1. Portfolio return `-22.16%`.
2. Sottoperforma cash, random baseline, equal-weight universe e ticker holding window.
3. Score profile non monotono; bucket score 100 negativo.
4. 142 rejection per `insufficient_funds`, quindi l'ordine dei trade e la gestione cash restano molto impattanti.
5. L'allargamento della watchlist elimina la falsa euforia della smoke precedente: l'edge non regge su un universo piu' ampio.

## Decisione metodologica

Non aggiungere ancora sector cap, random delay, survivorship sensitivity o opening regime check.

Prima serve correggere il livello precedente: scanner/ranking/triage. In particolare:

```text
small_cap_scanner_score non e' validato come monotono
portfolio construction perde su universo piu' ampio
cash starvation produce molte rejection
```

## Prossime azioni

1. Non usare `small_cap_scanner_score` per sizing o ranking live.
2. Progettare un nuovo score profile/triage o separare setup diversi invece di aggregarli in uno score unico.
3. Aggiungere una diagnostica cash starvation: quante opportunita' vengono perse per capitale gia' impegnato e quali avrebbero performato.
4. Solo dopo una nuova ipotesi di ranking, ripetere smoke ampia con lo stesso manifest/config hash comparabile.

Vedi [[2026-05-11-cascade-small-cap-ex-outlier-stress-test]], [[2026-05-10-cascade-small-cap-portfolio-diagnostics-smoke]], [[2026-05-11-claude-small-cap-run-manifest]], [[Roadmap-Master]], [[backlog]].