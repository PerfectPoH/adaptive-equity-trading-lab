---
tipo: struttura-vault
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [vault, struttura, organizzazione]
---

# Vault Structure

Questo vault deve restare una memoria operativa, non una discarica di output.

## Regola base

```text
Il vault contiene decisioni, contesto e report umani.
Gli artefatti generati restano in experiments/, data/ o dashboard/.
```

## Cartelle

| Cartella | Uso |
|---|---|
| `00-Progetto/` | Architettura, roadmap, regole, memoria AI e struttura del vault |
| `01-Feature/` | Specifiche vive di moduli o feature |
| `02-Devlog/YYYY-MM/` | Log cronologici delle sessioni |
| `03-Bug/` | Bug, rischi, tech debt e backlog |
| `04-Documentazione/Reports/` | Report di milestone, analisi e postmortem |
| `04-Documentazione/Handoff/` | Handoff lunghi per altre chat o agenti |
| `04-Documentazione/_archive/` | Documenti superati ma da conservare |

## Naming

Devlog:

```text
02-Devlog/YYYY-MM/YYYY-MM-DD-<agente>-<topic>.md
```

Report:

```text
04-Documentazione/Reports/Report-<topic>-YYYY-MM-DD.md
```

Handoff:

```text
04-Documentazione/Handoff/<Nome-Handoff>.md
```

Feature:

```text
01-Feature/<feature-name>.md
```

## Regole anti-caos

- Non creare nuovi file root salvo alias intenzionali come [[Roadmap]].
- Non usare nomi generici duplicati come `README.md` in piu' cartelle.
- Ogni devlog deve linkare almeno un documento vivo.
- Ogni report deve indicare run, test e decisione.
- Ogni nuova ipotesi strategica va nel vault, ma ogni CSV/JSON generato resta fuori dal vault.
- Se una nota diventa vecchia, archiviarla invece di cancellarla.

## Indici

- [[INDEX]] - ingresso principale.
- [[Devlog-Index]] - cronologia delle sessioni.
- [[Documentazione-Index]] - report e handoff.
- [[Wikilinks]] - nodi da tenere collegati nel grafo.
