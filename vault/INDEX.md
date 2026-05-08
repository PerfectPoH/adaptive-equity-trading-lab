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
>
> Per capire dove mettere una nota nuova, leggere [[Vault-Structure]].

---

## Quick links

- [[Protocollo-Collaborazione]] - ruoli, workflow, limiti operativi.
- [[Memoria-AI]] - errori da non ripetere e best practice.
- [[Architettura]] - struttura tecnica del sistema.
- [[Roadmap-Master]] - fasi del progetto e gate.
- [[Regole-Quant]] - regole anti-bias, backtest, execution e risk.
- [[Regole-Codice]] - regole pratiche per lavorare nel repo.
- [[Vault-Structure]] - regole per tenere ordinato il vault.
- [[backlog]] - bug, rischi aperti e tech debt.
- [[Report-Milestone1-2026-05-08]] - primo report operativo.
- [[Project-Handoff]] - handoff completo per altre chat o agenti.
- [[Devlog-Index]] - cronologia ordinata delle sessioni.
- [[Documentazione-Index]] - report e handoff ordinati.

---

## Struttura

| Cartella | Contenuto |
|---|---|
| `00-Progetto/` | Documenti fondazionali: architettura, roadmap, memoria AI, protocollo, regole, wikilinks |
| `01-Feature/` | Specifiche delle feature e dei moduli da costruire |
| `02-Devlog/YYYY-MM/` | Log cronologico delle sessioni, uno per sessione |
| `03-Bug/` | Backlog bug, rischi, tech debt e limiti noti |
| `03-Bug/_archive/` | Storico bug risolti quando il backlog cresce |
| `04-Documentazione/Reports/` | Report, analisi e postmortem |
| `04-Documentazione/Handoff/` | Handoff completi per altre chat o agenti |
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
- [[Vault-Structure]] - organizzazione e naming.
- [[Wikilinks]] - mappa dei nodi principali.

### 01-Feature

- [[mvp-core-pipeline]] - specifica della Milestone 1.
- [[news-risk-engine]] - filtro news/eventi, spostato dopo MVP.
- [[graphify-vault-memory]] - uso futuro di Graphify e vault.

### 02-Devlog

- [[Devlog-Index]] - cronologia delle sessioni.

### 03-Bug

- [[backlog]] - bug, rischi aperti, limiti noti.

### 04-Documentazione

- [[Documentazione-Index]] - indice report e handoff.
- [[Report-Milestone1-2026-05-08]] - stato della prima implementazione.
- [[Project-Handoff]] - riepilogo completo trasferibile ad altri agenti.
- [[README]] - note sulla cartella documentazione.

---

## Stato attuale

Milestone 1 e' stata scaffoldata e la pipeline gira end-to-end:

- test: `31 passed`;
- run pipeline default: `20260508_190512`;
- backtest out-of-sample 2024: non batte buy-and-hold;
- fallimento documentato: la baseline e' funzionante ma non ancora competitiva;
- default sperimentale corrente: `use_news=false`, `model_type=random_forest`, feature set baseline, isotonic calibration, `model_probability > 0.25`;
- diagnosi principale: 1093 segnali su 10 simboli, rendimento medio 2024 circa 6.99%, ma ancora sotto buy-and-hold;
- split temporale purgato: le ultime barre di train/validation/test vengono rimosse quando la label a 10 giorni supererebbe il confine;
- downloader robusto: se `yfinance` fallisce, usa l'ultimo snapshot locale valido;
- news GDELT macro 2020-2024 collegate come feature laggate sperimentali, non default.
- calibrazione isotonic implementata e promossa a default di ricerca dopo walk-forward;
- feature-regime analysis aggiornata: low rolling volatility, high distance-from-high e low calibrated probability sono bucket fragili.
- regime-filter validation aggiornata: i filtri non migliorano strategy return; combined filters migliorano drawdown ma tagliano troppo rendimento.
- walk-forward validation completata: default aggiornato a isotonic `0.25`; verdict `positive_but_under_benchmark`.
- model comparison completata: Logistic Regression e HistGradientBoosting non battono Random Forest sotto vincolo minimo di 30 trade validation.
- feature-set comparison completata: `enhanced_context` non viene promosso perche' peggiora il test 2024 rispetto al baseline default.

Conclusione: il progetto ha una base tecnica valida, ma i risultati non vanno interpretati come strategia pronta per capitale reale.

---

## Routine prima di lavorare

1. Apri [[INDEX]].
2. Leggi [[Protocollo-Collaborazione]].
3. Controlla [[Memoria-AI]] per anti-pattern gia' noti.
4. Controlla [[backlog]].
5. Se tocchi strategia, feature, label, risk o backtest, controlla [[Regole-Quant]].
6. A fine sessione aggiorna un devlog in `02-Devlog/YYYY-MM/`.
7. Se aggiungi documenti nuovi, aggiorna [[Devlog-Index]] o [[Documentazione-Index]].
