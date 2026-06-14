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

## Update - quarta slice replay

Stato aggiornato:

```text
COMMAND LOG / REPLAY EQUIVALENCE IMPLEMENTED
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
96228c7 Add command log replay equivalence
```

Verifica:

```text
scripts/check-toolchain.ps1 -> READY_FOR_CPP20_MVP
cmake --build build -> success
limitforge_tests.exe -> 21 tests, 0 failures
```

Slice implementata:

- `CommandType::{Submit, Cancel, Replace}`;
- command log append-only per submit/cancel/replace;
- `commands()` read-only;
- `OrderBook::replay(commands)`;
- replay che ricostruisce stesso state checksum;
- replay che ricostruisce stessa sequenza eventi;
- replay dei reject.

Limiti intenzionali:

- command log ancora in memoria, non serializzato;
- replay parte da zero, non ancora da snapshot;
- checksum copre lo stato resting e non un file snapshot;
- niente market state machine.

Prossima mossa tecnica:

```text
Add snapshot object, snapshot restore, snapshot+tail replay equivalence, and serialized command export later.
```

## Update - quinta slice snapshot

Stato aggiornato:

```text
SNAPSHOT / RESTORE / SNAPSHOT+TAIL REPLAY IMPLEMENTED
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
c4d538b Add snapshot restore and tail replay
```

Verifica:

```text
scripts/check-toolchain.ps1 -> READY_FOR_CPP20_MVP
cmake --build build -> success
limitforge_tests.exe -> 23 tests, 0 failures
```

Slice implementata:

- `Snapshot` object con resting orders, next command sequence, next event sequence e checksum;
- `snapshot()`;
- `OrderBook::restore(snapshot)`;
- `OrderBook::replay_from(snapshot, tail_commands)`;
- snapshot restore ricrea stato resting;
- snapshot + tail replay produce stesso checksum del full path;
- tail replay preserva la sequence degli eventi successivi al checkpoint.

Limiti intenzionali:

- snapshot ancora in memoria, non serializzato;
- snapshot non conserva event history pre-checkpoint;
- nessun file format stabile;
- nessuna compressione o schema versioning.

Prossima mossa tecnica:

```text
Add machine-readable exports for commands/snapshots and a small demo scenario.
```

## Update - sesta slice export e demo

Stato aggiornato:

```text
READABLE EXPORTS / MARKET-VS-LIMIT DEMO IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Slice implementata:

- export testuale deterministico dei command log;
- export testuale deterministico degli event log;
- export testuale deterministico degli snapshot;
- `build_market_vs_limit_demo()`;
- confronto market buy vs passive limit buy sulla stessa profondita';
- slippage market misurato rispetto al midpoint;
- queue risk esplicitato per l'ordine limite passivo.

Numeri demo:

```text
market buy quantity = 150
reference midpoint = 10000 ticks
market average fill = 10133 ticks
market slippage = 133 ticks
passive limit fill = 0
passive resting quantity = 150
```

Limiti intenzionali:

- export ancora stringhe deterministicamente leggibili, non formato file stabile;
- nessun versioning dello schema;
- nessun eseguibile demo ancora;
- nessun binding Python.

Prossima mossa tecnica:

```text
Add a runnable demo executable that writes command/event/snapshot artifacts for the market-vs-limit scenario.
```

## Update - settima slice demo executable

Stato aggiornato:

```text
RUNNABLE MARKET-VS-LIMIT ARTIFACT DEMO IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Slice implementata:

- API `write_market_vs_limit_demo_artifacts(output_dir)`;
- eseguibile `limitforge_demo`;
- export `summary.txt`;
- export `market_commands.csv`;
- export `market_events.csv`;
- export `market_snapshot.csv`;
- export `passive_commands.csv`;
- export `passive_events.csv`;
- export `passive_snapshot.csv`;
- artifact sample versionati in `examples/market_vs_limit/artifacts/`.

Output demo:

```text
reference_midpoint_ticks=10000
market_filled_quantity=150
market_average_fill_ticks=10133
market_slippage_ticks=133
passive_filled_quantity=0
passive_resting_quantity=150
```

Limiti intenzionali:

- depth ladder sintetico e fisso;
- artifact CSV/testo, non archivio replay stabile;
- nessuna UI;
- nessun multi-size slippage curve.

Prossima mossa tecnica:

```text
Add depth ladder/BBO export and a richer slippage report for multiple order sizes.
```

## Update - ottava slice slippage curve

Stato aggiornato:

```text
DEPTH LADDER / MULTI-SIZE SLIPPAGE CURVE IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Slice implementata:

- `DepthLevel`;
- `SlippageCurvePoint`;
- `build_demo_depth_ladder()`;
- `build_market_buy_slippage_curve(...)`;
- `render_depth_ladder(...)`;
- `render_slippage_curve(...)`;
- artifact `depth_ladder.csv`;
- artifact `slippage_curve.csv`;
- visibilita' del partial fill quando la size supera la profondita' ask.

Output slippage curve:

```text
requested_quantity,filled_quantity,average_fill_ticks,slippage_ticks
50,50,10100,100
100,100,10100,100
150,150,10133,133
250,200,10150,150
```

Limiti intenzionali:

- profondita' sintetica e fissa;
- nessun modello fee/rebate;
- nessun replenishment;
- nessun BBO time series.

Prossima mossa tecnica:

```text
Add explicit execution reports with realized spread, fill ratio, and market-impact fields.
```

## Update - nona slice execution report

Stato aggiornato:

```text
EXECUTION REPORT OBJECT / COST DIAGNOSTIC ARTIFACT IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Slice implementata:

- `ExecutionReport`;
- `build_market_buy_execution_report(...)`;
- `build_passive_limit_buy_execution_report(...)`;
- `render_execution_reports(...)`;
- artifact `execution_report.csv`;
- fill ratio in basis points;
- unfilled quantity;
- realized spread side-adjusted;
- market impact quote-based;
- passive queue outcome.

Output report:

```text
label,side,order_type,requested_quantity,filled_quantity,unfilled_quantity,fill_ratio_bps,average_fill_ticks,realized_spread_ticks,market_impact_ticks,passive_queue_outcome
market_buy,Buy,Market,150,150,0,10000,10133,133,100,not_passive
passive_limit_buy,Buy,Limit,150,0,150,0,none,0,0,resting_in_queue
```

Limiti intenzionali:

- realized spread misurato contro midpoint statico, non markout futuro;
- market impact basato solo su visible quote movement;
- queue outcome ancora label deterministica, non modello probabilistico di posizione in coda.

Prossima mossa tecnica:

```text
Add post-trade markout windows and adverse-selection diagnostics.
```

## Update - decima slice post-trade markout

Stato aggiornato:

```text
POST-TRADE MARKOUT / ADVERSE-SELECTION DIAGNOSTICS IMPLEMENTED
```

Repo:

```text
C:\Users\barak\Documents\Codici Scuola\limitforge
```

Branch:

```text
feat/mvp-core
```

Slice implementata:

- `PostTradeMarkout`;
- `build_market_buy_markouts(...)`;
- `render_markouts(...)`;
- artifact `markout_report.csv`;
- markout side-adjusted;
- adverse selection in ticks.

Output markout:

```text
label,horizon_steps,side,order_type,average_fill_ticks,future_midpoint_ticks,markout_ticks,adverse_selection_ticks
market_buy,1,Buy,Market,10133,10050,-83,83
market_buy,2,Buy,Market,10133,10200,67,0
```

Interpretazione:

- horizon 1: il midpoint futuro scende sotto il fill medio, quindi adverse selection = 83 ticks;
- horizon 2: il midpoint futuro sale sopra il fill medio, quindi markout favorevole = 67 ticks.

Limiti intenzionali:

- midpoint futuro sintetico e fisso;
- horizon ordinali, non timestamp reali;
- markout calcolato sull'average fill aggregato, non sui singoli child fills.

Prossima mossa tecnica:

```text
Add per-trade fill records so execution reports can explain every child fill, not only aggregate averages.
```
