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

## Update - prima slice C++20

Stato aggiornato:

```text
TOOLCHAIN READY / FIRST CORE SLICE IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Commit:

```text
a04b393 Build initial deterministic order book core
```

Verifica:

```text
scripts/check-toolchain.ps1 -> READY_FOR_CPP20_MVP
cmake --build build -> success
limitforge_tests.exe -> 10 tests, 0 failures
```

Slice implementata:

- CMake + Ninja project;
- minimal C++ test harness;
- integer tick/quantity types;
- validated limit/market orders;
- resting bid/ask book;
- aggressive buy matching against asks;
- partial fill and average fill price;
- monotonic sequence numbers, including rejects;
- initial event vocabulary.

Limiti intenzionali della slice:

- no cancel/replace yet;
- no FIFO by order id inside same price level yet;
- no sell-side aggressive matching yet;
- no append-only event log yet;
- no snapshot/replay checksum yet.

Prossima mossa tecnica:

```text
Add price-level FIFO, symmetric sell matching, cancel order, and event emission.
```

## Update - seconda slice order book

Stato aggiornato:

```text
FIFO BOOK / CANCEL / EVENT LOG SLICE IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Commit:

```text
31b8197 Add FIFO book queues cancel and event log
```

Verifica:

```text
scripts/check-toolchain.ps1 -> READY_FOR_CPP20_MVP
cmake --build build -> success
limitforge_tests.exe -> 15 tests, 0 failures
```

Slice implementata:

- price levels convertiti da quantita' aggregate a code FIFO;
- matching aggressivo simmetrico buy/sell;
- remaining quantity interrogabile per order id;
- cancel per ordini resting;
- cancel reject per order id assente;
- event log append-only in memoria;
- eventi base: accepted, rejected, canceled, trade;
- sequence evento distinta dalla sequence del comando.

Limiti intenzionali:

- cancel usa ancora scansione lineare, non `orders_by_id`;
- trade event aggrega il fill del comando, non ancora ogni singolo match contro resting order;
- niente replace;
- niente snapshot/replay checksum;
- niente market state machine.

Prossima mossa tecnica:

```text
Add replace, order-id index, per-match trade events, and deterministic replay checksum.
```

## Update - terza slice indexed book

Stato aggiornato:

```text
ORDER-ID INDEX / REPLACE / PER-MATCH EVENTS / CHECKSUM GROUNDWORK IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Commit:

```text
9efb718 Add replace indexed orders and checksum groundwork
```

Verifica:

```text
scripts/check-toolchain.ps1 -> READY_FOR_CPP20_MVP
cmake --build build -> success
limitforge_tests.exe -> 19 tests, 0 failures
```

Slice implementata:

- `orders_by_id` per lookup diretto degli ordini resting;
- duplicate resting order id reject;
- `replace(order_id, new_price, new_quantity)`;
- replace re-entering at the back of the new price level;
- trade event per ogni resting match, non evento aggregato;
- `state_checksum()` deterministico sullo stato del book;
- checksum cambia quando cambia il book.

Limiti intenzionali:

- replace non attraversa ancora il lato opposto come nuovo ordine aggressivo;
- checksum copre lo stato resting, non ancora l'intero event replay;
- non esiste ancora una funzione di replay da event log;
- non c'e' ancora snapshot serializzato.

Prossima mossa tecnica:

```text
Add replay command log, snapshot checksum, and invariant tests for replay equivalence.
```
