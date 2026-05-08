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
