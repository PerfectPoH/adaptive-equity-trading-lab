---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-06-14
agente: codex
tags: [devlog, limitforge, microstructure, capstone, systems]
---

# 2026-06-14 - LimitForge capstone spec

## Contesto

Dopo il lavoro sul portfolio GitHub e sulle repo principali, e' emerso un gap forte nel profilo tecnico:

```text
molto full-stack / data / quant / medical
manca un progetto systems low-level che mostri motori, strutture dati e performance
```

La proposta scelta e' LimitForge: un Market Microstructure Engine per simulare limit order book, matching, replay ed execution realism.

## Decisione

Registrata la nota feature:

```text
[[limitforge-market-microstructure-engine]]
```

Decisione centrale:

```text
C++20 deterministic core
Python research layer
UI dopo
```

Il progetto non deve promettere trading profittevole. Deve mostrare:

- matching engine;
- order book;
- event sequencing;
- snapshot/replay;
- slippage;
- partial fills;
- maker/taker;
- queue position futura;
- strategy execution realism.

## Perche' e' importante

Il Trading Lab ha dimostrato che senza dati e senza execution realism e' facile creare edge finti. LimitForge deve diventare il motore che spiega cosa succede sotto la candela:

```text
prezzo teorico != prezzo eseguibile
mid price != fill price
segnale != trade realmente ottenibile
```

## Cosa e' stato annotato

- mappa delle reference: Nasdaq OUCH/ITCH, Eurex ETI/EOBI, CME Globex;
- reference open source: Liquibook, SimpleOrderbook, OrderBook-rs, PythonMatchingEngine, ABIDES, hftbacktest;
- architettura ideale;
- scope MVP;
- invarianti da testare;
- event schema;
- market states;
- execution simulator;
- synthetic market generation;
- roadmap in cinque fasi;
- narrativa portfolio.

## Stato

```text
REPO INITIALIZED / TOOLCHAIN GATE BLOCKED
```

Repo locale creato:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Commit iniziale:

```text
10ec713 Initialize LimitForge design and toolchain gate
```

Sono stati creati solo:

- README;
- design doc;
- toolchain gate;
- piano implementativo TDD;
- script `scripts/check-toolchain.ps1`.

Nessun matching-engine production code e' stato scritto perche' la macchina non espone ancora una toolchain C++ valida.

Toolchain probe:

```text
FOUND: git
MISSING: cmake
MISSING: cl
MISSING: g++
MISSING: clang++
MISSING: ninja
Status: BLOCKED_TOOLCHAIN_MISSING
```

Decisione corretta: non scrivere core C++ alla cieca senza possibilita' di compilare/testare.

## Prossima mossa

Quando si decide di partire:

1. installare o agganciare una toolchain C++20 + CMake;
2. rieseguire `.\scripts\check-toolchain.ps1` in `limitforge`;
3. se il gate passa, seguire `docs/superpowers/plans/2026-06-14-limitforge-mvp.md`;
4. implementare il core solo con TDD: test failing prima, poi codice.
