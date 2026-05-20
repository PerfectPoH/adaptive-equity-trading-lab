# 2026-05-20 - XMOM Trial 001 forensics

## Contesto

Dopo `TRIAL-XMOM-001`, il risultato nominale era positivo ma falliva outlier stress. L'obiettivo era iniziare l'autopsia indipendente senza modificare la strategia.

## Cosa e' stato fatto

Aggiunto analyzer:

```text
src/experiments/xmom_trial_forensic_analyzer.py
```

Aggiunto test:

```text
tests/test_xmom_trial_forensic_analyzer.py
```

Generati artifact:

```text
experiments/runs/xmom_trial_001_20260520/trade_forensics_report.json
experiments/runs/xmom_trial_001_20260520/trade_forensics_report.md
experiments/runs/xmom_trial_001_20260520/trade_forensics_top_trades.csv
experiments/runs/xmom_trial_001_20260520/trade_forensics_non_top_trades.csv
```

## Risultato

```text
top_3_pnl: +159448.57
rest_pnl: -50085.32
top_3_contribution_pct: 145.80%
```

Top 3:

```text
AEHR 2025-09-02 -> 2025-10-01
CRMD 2025-05-01 -> 2025-06-02
CRMD 2025-04-01 -> 2025-05-01
```

## Prima interpretazione

Le prime fonti pubbliche indicano che i top winner erano vicini a catalyst specifici:

- CRMD: preliminary/Q1 2025 results, DefenCath rollout, profitability.
- AEHR: AI-processor burn-in evaluation/order narrative.

Questo non valida XMOM come edge. Suggerisce una domanda piu' precisa:

```text
Il segnale sta catturando momentum cross-sectional distribuito
oppure esposizione fortunata a catalyst company-specific?
```

## Decisione

Nessun Markov/HMM filter per salvare la run. Nessun paper/live. Prossimo lavoro ammesso: catalyst-aware forensic classification, poi eventuale trial separato preregistrato.

Vedi [[Report-XMOM-Trial-001-Forensic-Interpretation-2026-05-20]].
