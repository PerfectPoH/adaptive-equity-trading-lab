---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: capstone-proposed
data: 2026-06-14
tags: [limitforge, market-microstructure, order-book, matching-engine, execution, systems, portfolio]
---

# LimitForge - Market Microstructure Engine

## Sintesi

LimitForge e' il progetto capstone proposto per colmare il pezzo che manca al portfolio: sistemi low-level, microstruttura di mercato, execution realism e simulazione deterministica.

La decisione architetturale e':

```text
core serio nativo subito
scope MVP stretto
Python sopra per ricerca e demo
UI solo dopo determinismo, replay e metriche execution stabili
```

Stack raccomandato:

```text
C++20 core
Python research layer / bindings
React/Next UI dopo
```

Obiettivo non e' costruire un bot o promettere alpha. Obiettivo e' costruire una venue simulata abbastanza realistica da mostrare come ordini, spread, coda, fees, slippage, partial fills e market impact cambiano il risultato di una strategia.

## Perche' serve

Il Trading Lab ha mostrato un limite strutturale dei backtest basati su OHLCV:

```text
il backtest puo' dire "compra qui"
ma non dimostra se l'ordine sarebbe stato eseguito li'
```

LimitForge deve rispondere alle domande che il Trading Lab non puo' risolvere da solo:

- quanto slippage pago se uso market order?
- quanto cambia il prezzo medio quando consumo piu' livelli del book?
- una strategia e' profittevole solo perche' ignora spread e depth?
- cosa cambia tra maker e taker?
- quanto pesa la queue position?
- cosa succede se il book si svuota durante un evento?
- un segnale resta valido se simulo fill parziali, fees e latenza?

In altre parole:

```text
Trading Lab = decide quando vorrebbe entrare
LimitForge = verifica se, come e a che costo l'ordine entra davvero
```

## Mappa delle reference

Le reference utili non vanno trattate come lista infinita di repo, ma come tre famiglie.

### Venue reali e protocolli

Servono per imparare regole, stati di mercato, separazione order-entry/market-data e recovery.

Reference principali:

- Nasdaq OUCH: order entry, enter/replace/cancel/execution.
- Nasdaq ITCH / TotalView-ITCH: feed pubblico full-depth order-by-order, sequence number, timestamp.
- Nasdaq Opening/Closing Cross: aste, imbalance, prezzo indicativo.
- Eurex T7 ETI: interfaccia transazionale.
- Eurex EOBI: feed order-by-order, snapshot/incremental recovery.
- CME Globex: matching non sempre FIFO semplice, componenti pro-rata.

Lezione chiave:

```text
order entry e market data devono essere interfacce separate
matching policy non deve essere hardcoded
market state machine non e' opzionale nel lungo periodo
snapshot + replay sono parte del cuore del sistema
```

### Core open source

Servono per strutture dati, hot path e scelte performance.

Reference:

- Liquibook: core C++ header-only, depth book, notifiche accepted/rejected/fill/cancel, benchmark multi-milione insert/s.
- SimpleOrderbook: C++ + Python extension, ricco set di ordini, pre-allocation e callbacks.
- OrderBook-rs: reference Rust safety-first, thread-safety e strutture low-level.
- LOB Engine C++20 con SDK Python: esempio portfolio-grade di core nativo, replay, analytics, snapshot/resume e backtest execution.

Lezione chiave:

```text
un order book veloce non basta
ma il core deve restare piccolo, deterministico e testabile
```

### Simulatori e backtester microstrutturali

Servono per latenza, queue position, replay e modelli di fill.

Reference:

- PythonMatchingEngine: price-time cash equity, replay L3, latency, impact del proprio ordine sul replay.
- ABIDES / ABIDES-Markets / ABIDES-Gym: discrete-event simulation multi-agent in stile ITCH/OUCH.
- hftbacktest: queue model, latency model e fill realism per strategie passive.
- LOBSTER: ricostruzione order book da messaggi ITCH.
- Queue-reactive model: flussi d'ordine dipendenti dallo stato corrente del book.
- Optiver Ready Trader Go: exchange simulator didattico con fees, risk limits, wash trade rejection, rate limits e log.

Lezione chiave:

```text
execution realism vale piu' di una curva PnL bella
queue position e latency cambiano radicalmente i risultati
```

## Principi di progetto

### 1. Determinismo prima della velocita'

La prima release deve essere ripetibile:

```text
stesso input log -> stesso book finale -> stessi fill -> stesso checksum
```

Performance e UI vengono dopo.

### 2. Event log append-only

Ogni cambiamento di stato deve diventare evento sequenziato:

```text
ORDER_ACCEPTED
ORDER_REJECTED
ORDER_REPLACED
ORDER_CANCELED
ORDER_PARTIALLY_FILLED
ORDER_FILLED
TRADE
BBO_UPDATED
DEPTH_UPDATED
MARKET_STATE_CHANGED
SNAPSHOT_CREATED
```

### 3. Gateway unico

Le strategie non devono avere accesso privilegiato al book.

Devono:

```text
vedere market data
decidere
mandare ordini al gateway
aspettare latenza
entrare in coda
ricevere fill
pagare fee
```

Niente fill interni, niente futuro, niente scorciatoie da backtest.

### 4. Policy pluggable

Il matching iniziale sara' price-time priority, ma la policy deve poter cambiare:

```text
price-time
pro-rata
time-pro-rata
auction single-price
```

FIFO non e' una verita' universale.

### 5. Separazione order-entry / market-data

Il core deve distinguere:

```text
comandi privati: submit/cancel/modify
eventi privati: accepted/rejected/fill/cancel
market data pubblico: BBO/depth/trade tape/imbalance
```

Questa scelta ricalca la separazione venue-style OUCH/ITCH e ETI/EOBI.

## Architettura ideale

```text
limitforge/
  gateway/
    order_entry/
    validation/
    risk_checks/
    sequencer/

  core/
    order/
    price_level/
    order_book/
    matching/
    matching_policies/
    market_state_machine/
    ids/

  market_data/
    incremental_feed/
    snapshots/
    bbo_depth/
    trades_tape/
    imbalance/

  storage/
    event_log/
    snapshots/
    checksums/
    replay/

  sim/
    historical_adapters/
    synthetic_flow/
    latency/
    queue_models/
    fees/
    impact/
    regimes/
    execution/

  research/
    python_bindings/
    notebooks/
    strategies/

  api/
    websocket/
    http_read_only/

  ui/
    dashboard/
    replay/
    strategy_compare/

  tests/
    invariants/
    determinism/
    scenario_replay/
    performance/
```

Per l'MVP reale, questa struttura va ridotta, ma il disegno mentale resta questo.

## MVP stretto

Prima release:

```text
LimitForge v0.1
single-symbol deterministic C++20 matching engine
price-time limit order book
limit / market / cancel / replace
partial fill / full fill / reject
integer ticks
append-only event log
snapshot and replay
BBO + depth + trade tape
Python execution simulator
market order vs limit order slippage demo
invariant tests
```

Non fare subito:

- UI complessa;
- multi-symbol;
- networking;
- WebSocket;
- historical ITCH parser;
- ABIDES-like multi-agent;
- ottimizzazione 20M msg/s;
- ML/Kronos integration;
- strategie finanziarie elaborate.

## Strutture dati MVP

Versione semplice e corretta:

```text
unordered_map<OrderId, iterator> orders_by_id
std::map<Price, PriceLevel> bids
std::map<Price, PriceLevel> asks
std::list<Order> FIFO per price level
```

Regole:

- prezzi interni come integer ticks, non double;
- quantity come intero;
- order id univoco;
- sequence number monotono;
- FIFO dentro lo stesso livello di prezzo;
- market order non resta mai nel book;
- limit order non eseguito resta nel book;
- cancel rimuove solo ordini resting ancora vivi.

Ottimizzazioni future:

- dense price ladder;
- intrusive lists;
- memory pool;
- custom allocator;
- cache-friendly price levels.

## Invarianti da testare

Ogni test deve proteggere una regola di mercato.

Invarianti minime:

- best bid non puo' essere maggiore o uguale al best ask dopo matching continuo;
- un ordine cancellato non puo' essere fillato;
- market order non puo' restare nel book;
- limit order non aggressivo resta nel book;
- aggressive limit order consuma il lato opposto prima di restare;
- FIFO rispettato dentro lo stesso prezzo;
- quantita' totale coerente tra resting, filled, canceled e rejected;
- sequence number sempre crescente;
- replay completo e replay da snapshot producono stesso checksum;
- prezzo e quantita' non possono essere negativi;
- ordine con tick non valido viene rejected;
- ordine con quantity zero viene rejected;
- halt/closed state rifiuta ordini non consentiti.

## Market states

MVP:

```text
CONTINUOUS
HALTED
CLOSED
```

Roadmap:

```text
PRE_OPEN
OPENING_AUCTION
CONTINUOUS
HALTED
CLOSING_AUCTION
CLOSED
```

Le aste non entrano nel primo MVP, ma l'architettura non deve renderle impossibili.

## Execution simulator

Input:

```json
{
  "side": "BUY",
  "quantity": 1000,
  "order_type": "market",
  "timestamp": "09:31:04.200"
}
```

Output:

```json
{
  "requested_quantity": 1000,
  "filled_quantity": 1000,
  "average_price": 101.42,
  "arrival_mid": 101.10,
  "slippage_bps": 31.65,
  "fees": 2.00,
  "market_impact": 0.12,
  "status": "filled"
}
```

Demo essenziale:

```text
market order entra subito ma paga slippage
limit order paga meno ma rischia no-fill
```

Questa demo deve mostrare visivamente e numericamente perche' un backtest OHLCV ingenuo e' falso.

## Synthetic market generation

Non partire con Poisson casuale puro.

Generatore iniziale:

- stato del book;
- spread corrente;
- depth bid/ask;
- imbalance;
- regime;
- probabilita' di market order, limit order e cancel dipendenti dallo stato.

Regimi sintetici futuri:

```text
LIQUID_NORMAL
ILLIQUID_CHOP
OPENING_VOLATILITY
NEWS_SHOCK
PANIC_SELL
LOW_VOLUME_RANGE
```

## Roadmap

### Phase 1 - Core correctness

- C++20 book;
- limit/market/cancel/replace;
- event stream;
- invariant tests;
- deterministic replay.

### Phase 2 - Execution realism

- maker/taker fees;
- slippage metrics;
- passive fill model;
- queue position approximation;
- synthetic state-dependent order flow.

### Phase 3 - Python research layer

- pybind11 bindings;
- notebooks;
- execution reports;
- strategy comparison;
- examples.

### Phase 4 - Visual replay UI

- book ladder;
- trade tape;
- event timeline;
- strategy markers;
- slippage explanation;
- replay controls.

### Phase 5 - Advanced microstructure

- auctions;
- IOC/BOC/FOK;
- stop/OCO;
- pro-rata/time-pro-rata;
- self-match prevention;
- latency model;
- multi-agent simulation.

## Portfolio narrative

README story:

```text
Most retail backtests assume that a trade fills at the candle price.
LimitForge shows what actually happens when the order has to cross a book.
```

La demo ideale:

1. book iniziale;
2. market buy entra;
3. ask levels vengono consumati;
4. prezzo medio peggiora;
5. report mostra slippage e fees;
6. snapshot + replay producono stesso checksum.

Messaggio portfolio:

```text
Adaptive Equity Trading Lab = research governance
LimitForge = microstructure and execution engine
```

Questo chiude il cerchio tra finanza quantitativa e sistemi.

## Decisione finale registrata

```text
LimitForge sara' progettato come core C++20 deterministico con Python research layer.
La UI arrivera' dopo.
Il primo obiettivo e' correttezza, replayability e execution realism, non bellezza grafica o alpha.
```

## Prossima azione ammessa

Scrivere una design spec implementativa separata prima di creare codice:

```text
repo name
language/toolchain
MVP file structure
test framework
event schema
snapshot checksum rule
Python binding boundary
first demo scenario
```

Solo dopo la spec si apre la fase di implementazione.
