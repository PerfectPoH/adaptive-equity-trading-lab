---
tipo: documentazione-index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-21
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
