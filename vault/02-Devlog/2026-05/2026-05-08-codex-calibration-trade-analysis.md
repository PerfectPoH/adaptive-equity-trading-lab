---
tipo: devlog
data: 2026-05-08
agente: codex
topic: calibration-trade-analysis
tags: [devlog, calibration, trade-analysis, milestone2]
---

# Sessione Codex - Calibration e trade analysis

## Contesto

Dopo ablation e threshold validation, serviva capire due cose: se le probabilita' del modello sono affidabili e quali trade chiusi stanno guidando profitti/perdite.

## Cosa ho fatto

- Aggiunto `src/analysis/calibration.py`.
- Aggiunto `src/analysis/trade_analyzer.py`.
- Pipeline aggiornata con export:
  - `calibration.csv`
  - `calibration_summary.json`
  - `trades.csv`
  - `trade_analysis_by_symbol.csv`
  - `trade_analysis_summary.json`
- Dashboard aggiornata con calibration chart e trade-level analysis.
- Aggiunti test `test_calibration.py` e `test_trade_analyzer.py`.
- Aggiornati docs e vault.

## Risultati

Run default `20260508_174122`:

- Test: `16 passed`.
- Closed trades: 36.
- Wins: 23.
- Losses: 13.
- Trade win rate: circa 63.9%.
- Best trade: NVDA, segnale 2024-02-22, circa +12.79%.
- Worst trade: NVDA, segnale 2024-06-12, circa -6.89%.
- AMD e' l'unico simbolo con media trade negativa.

Calibration:

- Validation Brier: circa 0.238.
- Test Brier: circa 0.208.
- Le probabilita' raw del Random Forest sono overconfident.
- `model_probability` va trattato come ranking score, non come probabilita' reale.

## Prossima sessione consigliata

1. Implementare calibration layer fit solo su validation.
2. Confrontare raw vs calibrated su test.
3. Fare feature-regime analysis sui trade perdenti.
4. Capire se AMD va filtrato per volatilita'/regime o se e' solo rumore del campione.
