---
tipo: devlog-index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-11
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
- [[2026-05-10-cascade-small-cap-metadata-builder]] - builder CSV metadata small-cap da watchlist ticker con provider yfinance e diagnostica.
- [[2026-05-10-cascade-small-cap-one-shot-experiment]] - modalita' CLI one-shot da watchlist ticker a metadata CSV e report storico.
- [[2026-05-10-cascade-small-cap-smoke-runs]] - primi smoke run reali one-shot con diagnostica metadata, candidati e benchmark.
- [[2026-05-10-cascade-small-cap-report-diagnostics]] - report small-cap arricchito con universe/scanner/metadata diagnostics end-to-end.
- [[2026-05-10-cascade-small-cap-execution-planner-core]] - planner atomico candidate + next open + cash per execution reale.
- [[2026-05-10-cascade-small-cap-portfolio-backtester-core]] - portfolio backtester core con cash ledger, trade log, equity curve e rejection summary.
- [[2026-05-10-cascade-small-cap-portfolio-report-integration]] - integrazione portfolio nel runner/report storico con artefatti CSV e sezioni markdown.
- [[2026-05-10-cascade-small-cap-critical-diagnostics-roadmap]] - gate critico su outlier risk, score monotonicity e distinzione implementato/roadmap.
- [[2026-05-10-cascade-small-cap-portfolio-diagnostics-report]] - outlier P&L breakdown e score profile report integrati nel runner/report.
- [[2026-05-10-cascade-small-cap-portfolio-diagnostics-smoke]] - smoke reale con portfolio +74.25% ma verdetto non promuovere per outlier concentration.
- [[2026-05-11-cascade-small-cap-ex-outlier-stress-test]] - metriche ex-outlier: senza top 3 winner il portfolio passa a -0.64%.
- [[2026-05-11-claude-small-cap-run-manifest]] - run manifest small-cap con `run_id`, config hash SHA-256, periodo, universo e markdown section; chiude il gate per sweep tracciabili (RISK-023 mitigato).
- [[2026-05-11-cascade-small-cap-wide-smoke-diagnostics]] - smoke ampia su 30 ticker eleggibili: portfolio -22.16%, score non monotono.
- [[2026-05-11-cascade-small-cap-cash-starvation-diagnostics]] - missed opportunities sulle rejection cash: mediana -4.75%, win rate 38.03%.
- [[2026-05-11-cascade-small-cap-setup-disentangler-diagnostics]] - setup-level diagnostics passiva: breakout positivo, post-gap zavorra, score 100 non monotono.
- [[2026-05-11-cascade-small-cap-setup-feature-diagnostics]] - feature-level diagnostics per setup: regioni feature opposte e prossimo rule ablation passivo.
- [[2026-05-11-cascade-small-cap-breakout-only-ablation]] - ablation `allowed_setups=[breakout_continuation]`: +37.97% ma ancora outlier-driven.
- [[2026-05-11-cascade-small-cap-feature-filter-ablation]] - feature filters dentro breakout: `open_to_close_return>=0.084459` resta positivo senza top 3 winner.
- [[2026-05-11-cascade-small-cap-open-to-close-sensitivity]] - sensitivity soglie arrotondate: `open_to_close_return>=0.10` e' ipotesi primaria ma sample-small.
- [[2026-05-11-cascade-small-cap-temporal-split-validation]] - split H1/H2: edge `>=0.10` forte in H2 ma time-concentrated.
- [[2026-05-11-cascade-small-cap-multiyear-validation]] - multi-year 2022-2024: `>=0.10` sopravvive ex-top3 ma resta 2024-driven.
- [[2026-05-11-cascade-small-cap-regime-diagnostics]] - regime diagnostics passiva: IWM sopra EMA200 discrimina, EMA50/VIX no.
- [[2026-05-12-cascade-small-cap-ema200-regime-gate-ablation]] - regime_filters attivo EMA200: migliora P&L/ex-top3 ma resta 2024-driven.
- [[2026-05-12-cascade-small-cap-2023-false-positive-error-analysis]] - falsi positivi 2023: whipsaw IWM, nessun nuovo filtro, prossimo OOS congelato.
- [[2026-05-12-cascade-small-cap-oos-2025-h1-validation]] - OOS H1 2025 congelato: solo 2 trade, negativo, validation gate non superato.
- [[2026-05-12-cascade-small-cap-oos-2025-full-validation]] - OOS full-year 2025: 15 trade, ancora negativo, portfolio sotto benchmark filtrato.
- [[2026-05-12-cascade-small-cap-portfolio-mechanics-audit]] - audit sizing/cash: planner ignora risk_fraction, cash starvation salta candidati positivi.
- [[2026-05-12-cascade-small-cap-risk-based-sizing-fix]] - fix TDD sizing risk-based: OOS 2025 migliora ma resta outlier-dependent.
- [[2026-05-12-cascade-small-cap-multiyear-risk-sizing-rerun]] - rerun 2022-2024 EMA200 con sizing corretto: vecchio +169% crolla a +3.60%.
- [[2026-05-13-cascade-small-cap-setup-archive-decision]] - decisione finale: setup breakout EMA200 archiviato, ranking/uscite solo come track separato.
- [[2026-05-13-cascade-small-cap-ranking-exits-track-opened]] - apertura design-only del track ranking/uscite con trial accounting obbligatorio.
- [[2026-05-13-cascade-small-cap-trial-accounting-manifest]] - TDD: trial_accounting top-level nel run_manifest, separato dal config_hash.
- [[2026-05-13-cascade-small-cap-rankex-trial-001-preregistration]] - pre-registrazione TRIAL-RANKEX-001: ranking by scanner score, non run.
- [[2026-05-14-cascade-small-cap-rankex-trial-001-ranking-policy]] - TDD ranking policy TRIAL-RANKEX-001: tie-breaker deterministici, non run.
- [[2026-05-14-cascade-small-cap-rankex-trial-001-accounting-wiring]] - TDD payload trial_accounting canonico TRIAL-RANKEX-001 e forwarding, non run.
- [[2026-05-14-cascade-small-cap-rankex-trial-001-validation-command]] - comando validation preconfigurato TRIAL-RANKEX-001, non run.
- [[2026-05-14-cascade-small-cap-rankex-trial-001-validation-result]] - validation TRIAL-RANKEX-001 fallita ex-top3, stop/no OOS.
- [[2026-05-14-cascade-small-cap-rankex-strategic-decision]] - chiusura ranking semplice e prossima direzione cross-sectional momentum spec-only.
- [[2026-05-14-cascade-small-cap-data-quality-gate-decision]] - gate data-quality/methodology prima di nuovi trial small-cap.
- [[2026-05-14-cascade-small-cap-data-quality-audit-spec]] - spec audit yfinance small-cap pre-registrata, non eseguita.
- [[2026-05-15-cascade-small-cap-data-quality-audit-result]] - audit yfinance small-cap eseguito; verdict not usable for small-cap trials with yfinance daily alone.
- [[2026-05-15-cascade-small-cap-lessons-learned-data-quality]] - lessons learned data-quality; old small-cap work reclassified as methodology/infrastructure stress test.
- [[2026-05-15-cascade-nctrl-scaffolding-check]] - technical negative-control scaffolding check completed on fixed large-cap/ETF universe.
- [[2026-05-17-cascade-nctrl-property-check-infrastructure]] - TDD infrastructure complete for TRIAL-NCTRL-001 property checks, not executed.
- [[2026-05-17-cascade-nctrl-trial-001-property-check-result]] - TRIAL-NCTRL-001 executed once as property check; P1-P8 pass, no strategy promotion.
- [[2026-05-17-cascade-nctrl-program-status]] - NCTRL program closed as technical/methodology pass; next work is data/infra, not alpha sweep.
- [[2026-05-17-cascade-untracked-audit]] - audited `.windsurf/` and `data/`; small archival metadata/workflow files versioned, no strategy reopening.
- [[2026-05-17-cascade-data-provider-evaluation-plan]] - spec-only provider/data evaluation gate for future small-cap work; no provider selected or trial opened.
- [[2026-05-17-cascade-run-artifact-validator]] - TDD run artifact validator CLI added for post-run integrity checks.
- [[2026-05-17-cascade-methodology-gate-ledger]] - baseline multiple-testing/methodology ledger created; no new trial opened.
- [[2026-05-17-cascade-backtester-audit-plan]] - spec-only TDD audit plan for portfolio backtester mechanics after sizing bug.
- [[2026-05-17-cascade-backtester-audit-result]] - TDD backtester auditability fix; trade/rejection logs now preserve planner diagnostics.
- [[2026-05-17-cascade-data-provider-event-panel]] - provider evaluation event panel frozen before any provider query or selection.
- [[2026-05-17-cascade-data-provider-event-panel-expansion]] - provider event panel expansion slots filled and verified; `CCB` rejected, `ICU` substituted.
- [[2026-05-17-cascade-provider-evaluation-execution-checklist]] - provider evaluation execution checklist created; no provider query or selection.
- [[2026-05-17-cascade-provider-evaluation-artifact-validator]] - TDD provider evaluation artifact validator CLI added for future provider-evaluation outputs.
- [[2026-05-17-cascade-provider-evaluation-dry-run-template]] - dry-run provider evaluation artifact template created and validator-pass verified.

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
