---
tipo: protocollo
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [protocollo, agenti, workflow]
---

# Protocollo di Collaborazione

## 1. Ruoli

### Barak - Manager / Owner

- Decide obiettivi e priorita'.
- Approva passaggi rischiosi.
- Decide quando una fase e' abbastanza buona.
- Non deve essere spinto verso live trading.

### Codex - Executor tecnico locale

- Legge codice e vault prima di modificare.
- Implementa moduli piccoli e verificabili.
- Aggiorna test, documentazione e devlog.
- Non tocca progetti non richiesti.
- Non collega broker live senza richiesta esplicita.

### Altri modelli - Reviewer / Planner

- Possono proporre analisi, critique, roadmap e controlli.
- Le loro proposte vanno filtrate contro scope e milestone corrente.
- Se una proposta causa scope creep, va spostata in roadmap.

## 2. Regole vincolanti

- Prima il vault, poi il codice.
- Prima test e riproducibilita', poi performance.
- Prima paper/manuale, poi eventuale live.
- Nessuna promessa di profitti.
- Ogni modifica strategica deve avere log esperimento.
- Ogni fallimento importante va documentato.

## 3. Workflow standard

1. Leggere [[INDEX]], [[Memoria-AI]], [[Roadmap-Master]], [[backlog]].
2. Capire la milestone corrente.
3. Fare un cambiamento piccolo.
4. Eseguire test.
5. Se si cambia logica trading, eseguire pipeline.
6. Aggiornare vault e devlog.
7. Commit chiaro se il lavoro e' stabile.

## 4. Cosa nessun agente puo' fare

- Usare capitale reale senza consenso esplicito.
- Salvare chiavi broker/API in repo.
- Disabilitare risk manager per migliorare metriche.
- Usare il test set come validation nascosta.
- Nascondere un backtest brutto.
- Toccare `soresina-mercati` salvo nuova richiesta esplicita.

## 5. Gestione scope creep

Se nasce un'idea avanzata, scriverla in [[Roadmap-Master]] o in una nota `01-Feature/`, senza implementarla nella milestone corrente se non serve alla Definition of Done.

## 6. Quando aggiornare il vault

Aggiornare il vault quando cambia architettura, roadmap, viene scoperto un bias/bug, si chiude una milestone, un esperimento importante fallisce o riesce, o si prende una decisione che un agente futuro deve sapere.

## 7. Conflitti

Se chat e vault divergono, la chat piu' recente guida il lavoro immediato. Dopo l'azione, il vault va riallineato.

Vedi anche [[Memoria-AI]], [[Regole-Codice]], [[Regole-Quant]].
