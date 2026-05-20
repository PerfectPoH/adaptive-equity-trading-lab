---
tipo: documentazione-index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-20
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

## Handoff

- [[Project-Handoff]] - handoff aggiornato per altre chat o agenti, con stato small-cap corrente.

## Regole

- I report vanno in `04-Documentazione/Reports/`.
- Gli handoff vanno in `04-Documentazione/Handoff/`.
- Documenti superati vanno in `04-Documentazione/_archive/`.
- Le note brevi operative vanno nei devlog, non qui.

Vedi [[Vault-Structure]].
