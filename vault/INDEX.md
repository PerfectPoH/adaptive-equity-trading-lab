---
tipo: index
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [vault, index, obsidian, trading-lab]
---

# Indice - Vault Adaptive Equity Trading Lab

> Cervello condiviso del progetto. Questo vault tiene insieme architettura, fasi, memoria AI, errori gia' visti, report e decisioni operative.
>
> Prima di scrivere codice leggere sempre: [[Protocollo-Collaborazione]], [[Memoria-AI]], [[Roadmap-Master]], [[backlog]].

---

## Quick links

- [[Protocollo-Collaborazione]] - ruoli, workflow, limiti operativi.
- [[Memoria-AI]] - errori da non ripetere e best practice.
- [[Architettura]] - struttura tecnica del sistema.
- [[Roadmap-Master]] - fasi del progetto e gate.
- [[Regole-Quant]] - regole anti-bias, backtest, execution e risk.
- [[Regole-Codice]] - regole pratiche per lavorare nel repo.
- [[backlog]] - bug, rischi aperti e tech debt.
- [[Report-Milestone1-2026-05-08]] - primo report operativo.
- [[Project-Handoff]] - handoff completo per altre chat o agenti.

---

## Struttura

| Cartella | Contenuto |
|---|---|
| `00-Progetto/` | Documenti fondazionali: architettura, roadmap, memoria AI, protocollo, regole, wikilinks |
| `01-Feature/` | Specifiche delle feature e dei moduli da costruire |
| `02-Devlog/` | Log cronologico delle sessioni, uno per sessione |
| `03-Bug/` | Backlog bug, rischi, tech debt e limiti noti |
| `03-Bug/_archive/` | Storico bug risolti quando il backlog cresce |
| `04-Documentazione/` | Report, handoff, analisi e documenti vivi |
| `04-Documentazione/_archive/` | Documenti superati mantenuti per memoria |

---

## Documenti vivi

### 00-Progetto

- [[Architettura]] - stack e flusso dati.
- [[Roadmap-Master]] - milestone e definition of done.
- [[Memoria-AI]] - memoria operativa anti-errori.
- [[Protocollo-Collaborazione]] - come devono lavorare umano e agenti.
- [[Regole-Codice]] - convenzioni tecniche.
- [[Regole-Quant]] - regole quantitative e anti-bias.
- [[Wikilinks]] - mappa dei nodi principali.

### 01-Feature

- [[mvp-core-pipeline]] - specifica della Milestone 1.
- [[news-risk-engine]] - filtro news/eventi, spostato dopo MVP.
- [[graphify-vault-memory]] - uso futuro di Graphify e vault.

### 03-Bug

- [[backlog]] - bug, rischi aperti, limiti noti.

### 04-Documentazione

- [[Report-Milestone1-2026-05-08]] - stato della prima implementazione.
- [[Project-Handoff]] - riepilogo completo trasferibile ad altri agenti.
- [[README]] - note sulla cartella documentazione.

---

## Stato attuale

Milestone 1 e' stata scaffoldata e la pipeline gira end-to-end:

- test: `19 passed`;
- run pipeline default: `20260508_175742`;
- backtest out-of-sample 2024: non batte buy-and-hold;
- fallimento documentato: la baseline e' funzionante ma non ancora competitiva;
- default sperimentale corrente: `use_news=false`, raw `model_probability > 0.55`;
- diagnosi principale: 119 segnali su 9 simboli, ma ancora sotto buy-and-hold;
- news GDELT macro 2020-2024 collegate come feature laggate sperimentali, non default.
- calibrazione isotonic implementata e confrontata: migliora le probabilita', ma non il rendimento della strategia;
- decisione: la calibrazione resta tool di analisi, non default operativo.
- feature-regime analysis aggiunta: volume relativo basso e distanza dal massimo a 20 giorni mid/high sono ipotesi di fragilita' da testare.

Conclusione: il progetto ha una base tecnica valida, ma i risultati non vanno interpretati come strategia pronta per capitale reale.

---

## Routine prima di lavorare

1. Apri [[INDEX]].
2. Leggi [[Protocollo-Collaborazione]].
3. Controlla [[Memoria-AI]] per anti-pattern gia' noti.
4. Controlla [[backlog]].
5. Se tocchi strategia, feature, label, risk o backtest, controlla [[Regole-Quant]].
6. A fine sessione aggiorna un devlog in `02-Devlog/`.
