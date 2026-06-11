---
tipo: documentazione-index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-22
tags: [documentazione, index, report, handoff]
---

# Documentazione Index

Questa cartella contiene documenti lunghi e trasferibili: report, handoff, review e postmortem.

## Reports

- [[Report-Milestone1-2026-05-08]] - stato tecnico e risultati della prima pipeline.
- [[Quant-Research-Priorities-2026-05-09]] - valutazione consigli esterni e priorita' research validation.
- [[Report-Small-Cap-Research-Status-2026-05-12]] - stato aggiornato della track small-cap dopo OOS 2025 e fix risk-based sizing.
- [[Report-Post-Run-Validation-Gate-2026-05-20]] - gate post-run per coerenza artifact, execution guardrails e riconciliazione trade-log/summary.
- [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]] - gate data-ingestion per manifest, hash, schema OHLCV, sanity check prezzi e report pass richiesto dal pre-run gate.
- [[Report-XMOM-Data-Ingestion-Synthetic-Dry-Run-2026-05-20]] - prova isolata del data-ingestion gate su dati sintetici, senza sbloccare il trial reale.
- [[Report-XMOM-Real-Data-Ingestion-2026-05-20]] - ingestione reale Databento XMOM; data gate e pre-run gate passano, nessun backtest eseguito.
- [[Report-XMOM-Trial-001-Execution-2026-05-20]] - prima esecuzione preregistrata XMOM; primary metric positiva, ma outlier stress fallito e nessuna promozione.
- [[Report-XMOM-Trial-001-Forensic-Interpretation-2026-05-20]] - autopsia indipendente dei trade XMOM; top winner CRMD/AEHR vicini a catalyst, nessuna promozione.
- [[Report-XMOM-Catalyst-Classification-2026-05-20]] - classificazione manuale catalyst su tutti gli 11 trade XMOM; nessuna promozione.
- [[Report-XMOM-Catalyst-Trial-001-Preregistration-Spec-2026-05-20]] - preregistration spec-only per distinguere post-catalyst continuation da fade.
- [[Report-XMOM-Catalyst-Preregistration-Validator-2026-05-20]] - validator strutturale della preregistration catalyst-aware; 58 controlli passati.
- [[Report-XMOM-Catalyst-Feature-Rationale-2026-05-20]] - review teorica delle feature catalyst-aware; soglie operative non ancora finali.
- [[Report-XMOM-Catalyst-Implementation-Gate-Spec-2026-05-20]] - spec di implementazione DSR/CPCV con guardrail earnings extraction; non eseguibile.
- [[Report-DSR-PSR-Utilities-2026-05-20]] - utility PSR/DSR implementate e testate; non collegate al trial.
- [[Report-CPCV-Utilities-2026-05-20]] - utility CPCV con purging/embargo implementate e testate; non collegate al trial.
- [[Report-Effective-Trial-Count-Utilities-2026-05-21]] - stimatore del numero effettivo di trial indipendenti; non collegato al trial.
- [[Report-Synthetic-Statistical-Gate-Harness-2026-05-21]] - harness sintetico che collega CPCV, `N_eff` e DSR; non collegato al trial.
- [[Report-XMOM-Earnings-Provider-Selection-Gate-2026-05-21]] - gate per selezione provider earnings calendar; non interrogato.
- [[Report-XMOM-Earnings-Single-Probe-Approval-2026-05-21]] - artifact di approvazione per probe one-provider/one-symbol; validato ma non interrogato.
- [[Report-XMOM-Earnings-Single-Probe-Runner-Gate-2026-05-21]] - runner/preflight inerte per single probe; real-run bloccato.
- [[Report-XMOM-Earnings-Single-Probe-Execution-Preflight-2026-05-21]] - validator pre-esecuzione single probe; stato corrente bloccato.
- [[Report-XMOM-Earnings-Single-Probe-Explicit-Approval-Template-2026-05-21]] - template di approvazione esplicita single probe; non concesso.
- [[Report-XMOM-Earnings-Single-Probe-Theoretical-Review-2026-05-21]] - review teorica provider/simbolo Intrinio/CRMD; non approvata.
- [[Report-Earnings-Timestamp-Classifier-2026-05-21]] - utility locale per classificare timestamp earnings in BMO/AMC/DMT/UNSPECIFIED.
- [[Report-XMOM-Earnings-Single-Probe-Execution-2026-05-21]] - esecuzione bounded Intrinio/CRMD, HTTP 403 provider/access, no raw payload.
- [[Report-PEAD-SUE-Entitlement-Pack-2026-05-21]] - pack di domande provider, criteri e one-call probe spec per sbloccare SUE/PIT senza proxy.
- [[Report-Trade-Governance-Runtime-2026-05-21]] - runtime spec-only per GOOD/BAD trade tagging, BAD_WIN exclusion e cooldown post-stop.
- [[Report-Alpha-Candidate-Factory-2026-05-21]] - factory spec-only di 12 candidati alpha/probe ordinati per falsificabilita' e costo dati.
- [[Report-Outlier-Resistant-Diagnostic-Harness-2026-05-21]] - diagnostico ALPHA-009 su artifact esistenti; nessun superstite robusto.
- [[Report-Dollar-Bar-Diagnostic-2026-05-21]] - diagnostico ALPHA-003: dollar-bars migliorano stabilita' distributiva su 11/12 file, no alpha.
- [[Report-DollarBar-Transform-Preregistration-2026-05-21]] - preregistrazione transform statico/adattivo con sole metriche distributive, no PnL.
- [[Report-DollarBar-Transform-Validation-2026-05-21]] - validazione static vs EMA dollar-bars con sole metriche distributive; EMA rejected, no PnL.
- [[Report-DollarBar-MicroRev-Trial-2026-05-21]] - protocollo in 5 passi: static dollar-bars canoniche, EMA bloccata, MicroRev archiviata.
- [[Report-Amihud-Liquidity-Toxicity-Diagnostic-2026-05-22]] - diagnostico Amihud pre-entry su XMOM; liquidity toxicity filter non supportato.
- [[Report-SEC-8K-Event-Timing-Diagnostic-2026-05-22]] - diagnostico timing SEC 8-K su CRMD; event windows distintive ma sample insufficiente.
- [[Report-SEC-8K-Multisymbol-Event-Timing-Diagnostic-2026-05-22]] - diagnostico SEC 8-K multi-symbol; timing regime candidate, direzione ancora bloccata.
- [[Report-SEC8K-XMOM-Overlap-Diagnostic-2026-05-22]] - diagnostico overlap XMOM/SEC 8-K; supporta interpretazione catalyst storica, nessun filtro tradabile.
- [[Report-SEC8K-Direction-Tape-Oracle-Preregistration-2026-05-22]] - preregistrazione spec-only direzionale SEC 8-K Tape Oracle; esecuzione bloccata.
- [[Report-SEC8K-Tape-Oracle-Intraday-Data-Contract-2026-05-22]] - data-contract intraday RTH per SEC 8-K Tape Oracle; provider/query/backtest bloccati.
- [[Report-SEC8K-Tape-Oracle-Existing-Intraday-Backtest-2026-05-22]] - backtest bounded su artifact intraday esistenti; 1 evento purgato, no trade.
- [[Report-SEC8K-Tape-Oracle-Databento-Mini-Panel-Backtest-2026-05-22]] - mini-panel Databento bounded SEC 8-K Tape Oracle; netto negativo dopo costi, no promotion.
- [[Report-Quant-Hypothesis-Generation-And-Video-Research-2026-05-21]] - manifesto spec-only per generare ipotesi falsificabili e roadmap Anno 2.
- [[Report-Gap-Down-Reversion-Preregistration-2026-05-21]] - preregistrazione spec-only `TRIAL-GAPREV-001`, 43/43 pass.
- [[Report-GapRev-Intraday-Data-Contract-Gate-2026-05-21]] - gate data-contract intraday per GapRev, 35/35 pass, no query.

## Handoff

- [[Project-Handoff]] - handoff aggiornato per altre chat o agenti, con stato small-cap corrente.

## Regole

- I report vanno in `04-Documentazione/Reports/`.
- Gli handoff vanno in `04-Documentazione/Handoff/`.
- Documenti superati vanno in `04-Documentazione/_archive/`.
- Le note brevi operative vanno nei devlog, non qui.

Vedi [[Vault-Structure]].

## Voci aggiunte automaticamente (igiene vault 2026-06-11)

- [[Report-Active-Only-Momentum-Smoke-001-2026-05-24]] - Active Only Momentum Smoke 001.
- [[Report-Active-Only-Momentum-Smoke-Robustness-001-2026-05-24]] - Active Only Momentum Smoke Robustness 001.
- [[Report-Adjustment-Tradability-Policy-Spec-2026-05-18]] - Adjustment Tradability Policy Spec.
- [[Report-Approved-Mini-Panel-Provider-Sensitivity-Diagnostic-2026-05-18]] - Approved Mini Panel Provider Sensitivity Diagnostic.
- [[Report-Approved-Single-Provider-Sensitivity-Diagnostic-2026-05-18]] - Approved Single Provider Sensitivity Diagnostic.
- [[Report-Backtester-Audit-Plan-2026-05-17]] - Backtester Audit Plan.
- [[Report-Backtester-Audit-Result-2026-05-17]] - Backtester Audit Result.
- [[Report-Credential-Preflight-Env-File-Pass-2026-05-18]] - Credential Preflight Env File Pass.
- [[Report-Credential-Preflight-Local-Result-2026-05-18]] - Credential Preflight Local Result.
- [[Report-DPE-Data-Quality-Audit-Interpretation-2026-05-18]] - DPE Data Quality Audit Interpretation.
- [[Report-DPE-Data-Quality-Audit-Layer-2026-05-18]] - DPE Data Quality Audit Layer.
- [[Report-Databento-Provider-Evaluation-Preflight-2026-05-17]] - Databento Provider Evaluation Preflight.
- [[Report-Dry-Run-Preflight-Spec-2026-05-18]] - Dry Run Preflight Spec.
- [[Report-Execution-Command-Output-Schema-Spec-2026-05-18]] - Execution Command Output Schema Spec.
- [[Report-Explicit-Execution-Authorization-Spec-2026-05-18]] - Explicit Execution Authorization Spec.
- [[Report-Explicit-Run-Approval-Preexecution-Preparation-2026-05-18]] - Explicit Run Approval Preexecution Preparation.
- [[Report-Final-Command-Review-Spec-2026-05-18]] - Final Command Review Spec.
- [[Report-First-Preregistered-Provider-Aware-Research-Plan-2026-05-18]] - First Preregistered Provider Aware Research Plan.
- [[Report-Form4-Cluster-Buying-Run-001-Parser-Failure-2026-05-23]] - Form4 Cluster Buying Run 001 Parser Failure.
- [[Report-Form4-Cluster-Buying-Trial-001-2026-05-23]] - Form4 Cluster Buying Trial 001.
- [[Report-Form4-Cluster-Buying-Trial-001-Clean-Rerun-2026-05-23]] - Form4 Cluster Buying Trial 001 Clean Rerun.
- [[Report-GapRev-End-To-End-Controlled-Run-2026-05-21]] - GapRev End To End Controlled Run.
- [[Report-GapRev-Event-Selection-Probe-2026-05-21]] - GapRev Event Selection Probe.
- [[Report-GapRev-Failure-Taxonomy-2026-05-21]] - GapRev Failure Taxonomy.
- [[Report-GapRev-Mini-Panel-Probe-2026-05-21]] - GapRev Mini Panel Probe.
- [[Report-Governance-Calibration-Falsifiability-Spec-2026-05-18]] - Governance Calibration Falsifiability Spec.
- [[Report-Graphify-Integration-Gate-2026-05-23]] - Graphify Integration Gate.
- [[Report-Graphify-Source-Scan-Smoke-Test-2026-05-23]] - Graphify Source Scan Smoke Test.
- [[Report-House-Portfolio-Trial-2026-06-11]] - House Portfolio Trial.
- [[Report-Intrinio-One-Event-Probe-Result-2026-05-17]] - Intrinio One Event Probe Result.
- [[Report-Intrinio-Provider-Evaluation-Preflight-2026-05-17]] - Intrinio Provider Evaluation Preflight.
- [[Report-Kronos-Defense-Duel-2026-06-11]] - Kronos Defense Duel.
- [[Report-Lab-Final-Status-Pack-001-2026-05-25]] - Lab Final Status Pack 001.
- [[Report-LowVol-Tradability-Trial-001-2026-05-23]] - LowVol Tradability Trial 001.
- [[Report-Manual-Preflight-Inputs-Resolution-Spec-2026-05-18]] - Manual Preflight Inputs Resolution Spec.
- [[Report-Market-Impact-Diagnostics-2026-05-20]] - Market Impact Diagnostics.
- [[Report-Methodology-Gate-Ledger-2026-05-17]] - Methodology Gate Ledger.
- [[Report-Mini-Panel-Approval-Gate-2026-05-18]] - Mini Panel Approval Gate.
- [[Report-Negative-Control-Program-Status-2026-05-17]] - Negative Control Program Status.
- [[Report-Negative-Control-Scaffolding-Check-2026-05-15]] - Negative Control Scaffolding Check.
- [[Report-Negative-Control-Trial-001-Preregistration-2026-05-15]] - Negative Control Trial 001 Preregistration.
- [[Report-Negative-Control-Trial-001-Property-Check-Result-2026-05-17]] - Negative Control Trial 001 Property Check Result.
- [[Report-New-Provider-Aware-Research-Track-Spec-2026-05-18]] - New Provider Aware Research Track Spec.
- [[Report-Old-Signal-Price-Replay-Full-Coverage-2026-05-18]] - Old Signal Price Replay Full Coverage.
- [[Report-Old-Strategy-Archive-Provider-Sensitive-2026-05-18]] - Old Strategy Archive Provider Sensitive.
- [[Report-Opening-Reclaim-Intraday-Probe-2026-05-21]] - Opening Reclaim Intraday Probe.
- [[Report-PEAD-AlphaVantage-Earnings-Probe-2026-05-23]] - PEAD AlphaVantage Earnings Probe.
- [[Report-PEAD-Earnings-Only-Gate-2026-05-21]] - PEAD Earnings Only Gate.
- [[Report-PEAD-Earnings-Source-Probe-2026-05-23]] - PEAD Earnings Source Probe.
- [[Report-PEAD-Free-Source-Scan-2026-05-23]] - PEAD Free Source Scan.
- [[Report-PEAD-SEC-Event-Source-Gate-2026-05-21]] - PEAD SEC Event Source Gate.
- [[Report-PEAD-SUE-Provider-Gate-2026-05-21]] - PEAD SUE Provider Gate.
- [[Report-Polygon-Active-Only-Exploratory-Policy-Gate-2026-05-24]] - Polygon Active Only Exploratory Policy Gate.
- [[Report-Polygon-Active-Universe-Seed-001-2026-05-24]] - Polygon Active Universe Seed 001.
- [[Report-Polygon-Delisted-Listing-Date-Probe-001-2026-05-24]] - Polygon Delisted Listing Date Probe 001.
- [[Report-Polygon-Delisted-Survivorship-Audit-001-2026-05-24]] - Polygon Delisted Survivorship Audit 001.
- [[Report-Polygon-Grouped-Daily-Liquidity-Probe-001-2026-05-24]] - Polygon Grouped Daily Liquidity Probe 001.
- [[Report-Polygon-Listing-Date-Combined-Policy-Gate-2026-05-24]] - Polygon Listing Date Combined Policy Gate.
- [[Report-Polygon-Listing-Date-Coverage-Continuation-001-2026-05-24]] - Polygon Listing Date Coverage Continuation 001.
- [[Report-Polygon-Listing-Date-Coverage-Probe-001-2026-05-24]] - Polygon Listing Date Coverage Probe 001.
- [[Report-Polygon-PIT-Construction-Method-Gate-2026-05-24]] - Polygon PIT Construction Method Gate.
- [[Report-Polygon-PIT-Membership-Policy-Gate-001-2026-05-24]] - Polygon PIT Membership Policy Gate 001.
- [[Report-Polygon-Stocks-Basic-Free-Preflight-2026-05-18]] - Polygon Stocks Basic Free Preflight.
- [[Report-Polygon-Ticker-Details-Listing-Date-Probe-001-2026-05-24]] - Polygon Ticker Details Listing Date Probe 001.
- [[Report-Polygon-Ticker-Reference-Probe-001-2026-05-24]] - Polygon Ticker Reference Probe 001.
- [[Report-Polygon-Universe-Quality-Probe-001-2026-05-24]] - Polygon Universe Quality Probe 001.
- [[Report-Pre-Execution-Output-Ledger-Gate-2026-05-18]] - Pre Execution Output Ledger Gate.
- [[Report-Provider-Combo-Gate-Databento-Polygon-2026-05-18]] - Provider Combo Gate Databento Polygon.
- [[Report-Provider-Coverage-Contract-Spec-2026-05-18]] - Provider Coverage Contract Spec.
- [[Report-Provider-Credential-Preflight-No-Query-2026-05-18]] - Provider Credential Preflight No Query.
- [[Report-Provider-Evaluation-Artifact-Validator-2026-05-17]] - Provider Evaluation Artifact Validator.
- [[Report-Provider-Evaluation-Dry-Run-Template-2026-05-17]] - Provider Evaluation Dry Run Template.
- [[Report-Provider-Evaluation-Runbook-2026-05-17]] - Provider Evaluation Runbook.
- [[Report-Provider-Join-Feasibility-2026-05-18]] - Provider Join Feasibility.
- [[Report-Provider-Sensitivity-Coverage-Aware-Expansion-2026-05-18]] - Provider Sensitivity Coverage Aware Expansion.
- [[Report-Provider-Sensitivity-Diagnostic-Runner-Dry-Only-2026-05-18]] - Provider Sensitivity Diagnostic Runner Dry Only.
- [[Report-Provider-Sensitivity-Micro-Check-Result-2026-05-18]] - Provider Sensitivity Micro Check Result.
- [[Report-Provider-Sensitivity-Real-Runner-Gated-2026-05-18]] - Provider Sensitivity Real Runner Gated.
- [[Report-Provider-Sensitivity-Test-Spec-2026-05-18]] - Provider Sensitivity Test Spec.
- [[Report-Quant-Research-Architecture-Upgrade-Plan-2026-05-17]] - Quant Research Architecture Upgrade Plan.
- [[Report-RESEARCH-062-Purged-Temporal-Split-Embargo-Validator-2026-05-18]] - RESEARCH 062 Purged Temporal Split Embargo Validator.
- [[Report-RESEARCH-100-Intrinio-EOD-Trial-Onboarding-Gate-2026-05-18]] - RESEARCH 100 Intrinio EOD Trial Onboarding Gate.
- [[Report-Reference-Data-Provider-Scan-001-2026-05-24]] - Reference Data Provider Scan 001.
- [[Report-Regime-Map-Diagnostic-001-2026-05-24]] - Regime Map Diagnostic 001.
- [[Report-Research-Program-Transition-Policy-Gate-2026-05-24]] - Research Program Transition Policy Gate.
- [[Report-Research-Run-Gate-Spec-2026-05-18]] - Research Run Gate Spec.
- [[Report-Run-Artifact-Validator-2026-05-17]] - Run Artifact Validator.
- [[Report-SEC-Company-Tickers-Universe-Probe-001-2026-05-24]] - SEC Company Tickers Universe Probe 001.
- [[Report-SEC-EDGAR-Earnings-Provider-Probe-2026-05-21]] - SEC EDGAR Earnings Provider Probe.
- [[Report-SEC8K-Directional-Alpha-Retirement-2026-05-23]] - SEC8K Directional Alpha Retirement.
- [[Report-SEC8K-Mini-Panel-Protocol-Violation-2026-05-23]] - SEC8K Mini Panel Protocol Violation.
- [[Report-SEC8K-Predrift-Existing-Daily-Diagnostic-2026-05-23]] - SEC8K Predrift Existing Daily Diagnostic.
- [[Report-SEC8K-Tape-Oracle-Clean-Run-002-2026-05-23]] - SEC8K Tape Oracle Clean Run 002.
- [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]] - Small Cap Data Provider Evaluation Plan.
- [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]] - Small Cap Data Provider Event Panel.
- [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]] - Small Cap Data Provider Event Panel Expansion.
- [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]] - Small Cap Data Quality Audit Result.
- [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]] - Small Cap Data Quality Audit Spec.
- [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]] - Small Cap Data Quality Gate Decision.
- [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]] - Small Cap Lessons Learned Data Quality.
- [[Report-Small-Cap-Provider-Evaluation-Execution-Checklist-2026-05-17]] - Small Cap Provider Evaluation Execution Checklist.
- [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]] - Small Cap RankEx Strategic Decision.
- [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]] - Small Cap RankEx Trial 001 Preregistration.
- [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]] - Small Cap RankEx Trial 001 Validation.
- [[Report-Studio-OOS-Preregistered-Rule-2026-06-11]] - Studio OOS Preregistered Rule.
- [[Report-Studio-OOS-Replication-2026-06-11]] - Studio OOS Replication.
- [[Report-Studio-OOS-Validation-2026-06-11]] - Studio OOS Validation.
- [[Report-Studio-OOS-VolNorm-Replication-2026-06-11]] - Studio OOS VolNorm Replication.
- [[Report-Transition-Five-Point-Batch-001-2026-05-24]] - Transition Five Point Batch 001.
- [[Report-Trial-Accounting-Preregistration-Spec-2026-05-18]] - Trial Accounting Preregistration Spec.
- [[Report-Universe-Expansion-Gate-001-2026-05-24]] - Universe Expansion Gate 001.
