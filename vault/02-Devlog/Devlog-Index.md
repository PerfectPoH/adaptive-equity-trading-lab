---
tipo: devlog-index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [devlog, index, cronologia]
---

# Devlog Index

I devlog sono ordinati per mese. Ogni file descrive una sessione concreta: cosa e' stato fatto, test eseguiti, risultati e decisioni.

## 2026-05

- [[2026-05-08-codex-milestone1-vault-init]] - inizializzazione vault e Milestone 1.
- [[2026-05-08-codex-analysis-dashboard-hardening]] - hardening dashboard e analisi run.
- [[2026-05-08-codex-news-features-and-ambiguity-skip]] - news feature e skip conservativo daily OHLC.
- [[2026-05-08-codex-ablation-threshold-validation]] - ablation news e threshold validation.
- [[2026-05-08-codex-calibration-trade-analysis]] - calibration report e trade-level analysis.
- [[2026-05-08-codex-calibration-layer-comparison]] - confronto raw vs calibrated.
- [[2026-05-08-codex-feature-regime-analysis]] - feature-regime analysis sui trade.
- [[2026-05-08-codex-regime-filter-validation]] - validazione filtri volume, distance e ATR.
- [[2026-05-08-codex-purged-calibrated-walk-forward]] - purge anti-leak, fallback snapshot e default calibrato.
- [[2026-05-08-codex-model-comparison]] - confronto walk-forward tra Logistic Regression, Random Forest e HistGradientBoosting.
- [[2026-05-08-codex-feature-set-comparison]] - confronto baseline feature set vs enhanced context.
- [[2026-05-08-codex-target-exit-comparison]] - timeout coerente nel backtest e confronto target/exit ATR.
- [[2026-05-08-codex-signal-quality-ranking]] - score qualita' segnale e confronto ranking giornaliero top-N.
- [[2026-05-08-codex-market-exposure-comparison]] - confronto risk fraction e scaling in regime SPY forte.
- [[2026-05-08-codex-universe-selection-comparison]] - confronto universi selezionati solo da validation.
- [[2026-05-08-codex-benchmark-objective-comparison]] - confronto obiettivi ML benchmark-aware.
- [[2026-05-08-cascade-model-registry]] - registry append-only dei modelli joblib con hash e metadata.
- [[2026-05-08-cascade-threshold-config]] - soglie scanner/modello versionate e tracciate nei log.
- [[2026-05-08-cascade-walk-forward-fold-builder]] - generatore riusabile di fold annuali walk-forward.
- [[2026-05-08-cascade-hyperparameter-comparison]] - confronto iperparametri Random Forest selezionati solo su validation.
- [[2026-05-09-cascade-temporal-embargo]] - embargo configurabile per split temporali e fold walk-forward.
- [[2026-05-09-cascade-backtest-analysis]] - notebook/report per diagnosi della sottoperformance backtest.
- [[2026-05-09-cascade-small-cap-pivot]] - pivot strategico verso research track long-only small/mid-cap swing.
- [[2026-05-09-cascade-small-cap-universe-builder]] - universe builder con filtri hard-coded e diagnostica rejection reasons.
- [[2026-05-09-cascade-small-cap-data-quality]] - report qualita' dati OHLCV per candidati small/mid-cap.
- [[2026-05-09-cascade-market-regime-guardrail]] - no-trade guardrail operativo per IWM, VIX e breadth.
- [[2026-05-09-cascade-small-cap-swing-scanner]] - scanner rule-based long-only per panic reversal, breakout continuation e post-gap drift.
- [[2026-05-09-cascade-small-cap-execution]] - execution planner conservativo con gap, costi e liquidity cap.
- [[2026-05-09-cascade-small-cap-candidate-export]] - export candidati giornalieri con diagnostica operativa.
- [[2026-05-09-cascade-small-cap-benchmarks]] - benchmark coerenti per small-cap: IWM, equal-weight, random baseline, holding-window e cash.
- [[2026-05-09-cascade-small-cap-backtest-report]] - report/proxy small-cap con verdict vs benchmark primario e diagnostica setup/regime/execution.
- [[2026-05-09-cascade-small-cap-historical-runner]] - runner storico end-to-end per candidate export, benchmark report e markdown report.
- [[2026-05-10-cascade-small-cap-data-preparer]] - preparer deterministico da OHLCV + metadata statici a input compatibili col runner storico.
- [[2026-05-10-cascade-small-cap-experiment-cli]] - orchestratore CLI per metadata CSV, download OHLCV/IWM/VIX, preparer e historical runner.

## Convenzione

Nuovi devlog:

```text
02-Devlog/YYYY-MM/YYYY-MM-DD-<agente>-<topic>.md
```

Ogni devlog deve contenere:

- contesto;
- cosa e' cambiato;
- verifiche;
- risultati;
- decisione o prossima mossa.

Vedi [[Vault-Structure]].
