# 2026-05-20 - XMOM catalyst classification

## Contesto

Dopo l'autopsia top-3 di `TRIAL-XMOM-001`, serviva classificare manualmente tutti gli 11 trade per capire se i winner erano legati a catalyst osservabili ex-ante o solo a eventi casuali durante il trade.

## Cosa e' stato fatto

Creati artifact:

```text
experiments/runs/xmom_trial_001_20260520/trade_forensics_catalyst_log.csv
experiments/runs/xmom_trial_001_20260520/trade_forensics_catalyst_summary.md
```

Creato report:

```text
vault/04-Documentazione/Reports/Report-XMOM-Catalyst-Classification-2026-05-20.md
```

## Risultato

```text
11/11 trades: company-specific narrative observable before entry
7/11 trades: major issuer event during holding window
top 3 winners: catalyst-adjacent
```

Ma catalyst exposure non basta:

```text
CRMD 2025-03-03 -> 2025-04-01: -52688.38
AEHR 2025-10-01 -> 2025-10-30: -35910.76
```

## Decisione

La domanda di ricerca cambia:

```text
Can a preregistered catalyst-aware momentum rule distinguish continuation from post-catalyst fade?
```

Blocco ancora valido:

```text
no paper trading
no live trading
no Markov/HMM patch
no post-hoc tuning
no strategy promotion
```

Prossimo lavoro ammesso: spec preregistrata, non esecuzione.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
