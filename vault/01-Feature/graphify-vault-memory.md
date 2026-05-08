---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: futuro
ultimo-aggiornamento: 2026-05-08
tags: [graphify, vault, memoria, codegraph]
---

# Feature - Graphify + Vault Memory

## Obiettivo

Usare Graphify come strumento esterno per trasformare il codice in un grafo interrogabile, mentre il vault resta la memoria umana/manuale del progetto.

## Decisione

- Il vault contiene decisioni, roadmap, report, errori e best practice.
- Graphify contiene il grafo generato dal codice.
- Gli output generati non devono sporcare il vault.
- Graphify non e' runtime del trading system.

## Uso futuro

1. Configurare Graphify sul repo.
2. Escludere `.venv*`, snapshot, cache, run, vault e file pesanti.
3. Generare report in una cartella tipo `graphify-out/`.
4. Aggiornare [[Memoria-AI]] con i comandi stabili.
5. Far leggere agli agenti sia vault sia report Graphify prima di refactor importanti.

## Anti-pattern

- Non mettere artefatti Graphify dentro `vault/`.
- Non usare Graphify per sostituire documentazione ragionata.
- Non generare grafo prima che il codice abbia abbastanza complessita' da giustificarlo.

Vedi [[Memoria-AI]] e [[Protocollo-Collaborazione]].
