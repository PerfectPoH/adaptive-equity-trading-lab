---
tipo: feature-spec
stato: proposed
progetto: adaptive-equity-trading-lab
data: 2026-05-09
tags: [feature, research-track, small-cap, swing, long-only]
---

# Small-Cap Swing Research Spec

## Decisione strategica

La baseline large-cap ML resta valida come controllo negativo, ma viene sospesa come area principale di ottimizzazione. I risultati documentati indicano che continuare a ruotare soglie, iperparametri e filtri sulla stessa baseline rischia di diventare data-mining.

Nuova research track: strategie **long-only** su small/mid-cap liquide, orientate a swing trade multiday e inefficienze comportamentali.

Non si implementano short nella prima fase.

## Obiettivo

Costruire una pipeline di ricerca per trovare setup long-only dove un trader retail puo' avere vantaggio strutturale:

- panic reversal;
- breakout continuation;
- post-gap drift long-only;
- volume/catalyst continuation;
- squeeze participation senza shortare.

L'obiettivo iniziale non e' battere SPY a ogni costo, ma capire se esiste un edge robusto rispetto a benchmark coerenti con small/mid-cap.

## Non-obiettivi

- Niente short selling nella fase iniziale.
- Niente hard-to-borrow modeling nella fase iniziale, salvo nota di rischio.
- Niente live trading.
- Niente uso di capitale reale.
- Niente deep learning prima di scanner, dati e label puliti.
- Niente micro-cap ultra-illiquide senza filtri di liquidita'.
- Niente promozione strategia da un singolo backtest.

## Universo iniziale

Criteri candidati da validare:

- azioni US small/mid-cap;
- market cap indicativa: 100M - 5B USD;
- prezzo minimo: preferibilmente sopra 2 USD o 5 USD, da testare;
- dollar volume medio minimo;
- volume medio minimo;
- esclusione ETF;
- esclusione strumenti con dati chiaramente rotti;
- esclusione opzionale ADR e biotech troppo binarie nella prima versione.

## Setup iniziali

### 1. Panic Reversal

Idea: comprare panico eccessivo su titolo ancora liquidabile, con segnale di stabilizzazione.

Feature candidate:

- gap down;
- drawdown a 5/20/60 giorni;
- distanza dal minimo intraday;
- close position nel range giornaliero;
- volume relativo;
- ATR percentuale;
- recupero dal low;
- market regime small-cap.

### 2. Breakout Continuation

Idea: comprare rotture con volume dove il mercato sta rivalutando il titolo.

Feature candidate:

- close vicino high;
- volume spike;
- range expansion;
- rottura massimo 20/60 giorni;
- consolidamento precedente;
- volatilita' compressa prima del breakout;
- float rotation proxy.

### 3. Post-Gap Drift Long-Only

Idea: evitare l'open caotico e studiare se alcuni gap con volume continuano nei giorni successivi.

Feature candidate:

- gap percentuale;
- open-to-close behavior;
- close position nel daily range;
- volume relativo;
- no-trade se open gap troppo estremo;
- no-trade se spread/slippage stimato troppo alto.

## Execution assumptions

La vecchia regola `next open` non e' automaticamente valida su small-cap.

Prima versione conservative:

- long-only;
- niente market order simulati ingenuamente;
- simulare spread/slippage conservativo;
- filtrare trade se gap di apertura supera soglia massima;
- valutare entry MOC o next-day limit logic;
- no fill se volume/dollar volume insufficiente;
- max position size vincolata alla liquidita'.

## Risk controls obbligatori

### Spread e slippage

Ogni backtest deve includere haircut conservativo. Se l'edge medio per trade e' inferiore allo spread/slippage stimato, il setup non e' valido.

### Offering e dilution risk

Rischio critico su small/micro-cap. Dati gratuiti non bastano per modellarlo bene.

Proxy iniziali:

- float rotation;
- volume anomalo multiplo del float;
- aumento volume senza continuita' prezzo;
- gap/spike e close debole;
- esclusione settori/ticker con pattern di dilution se noto.

### Capacity constraint

Regola proposta:

```text
position_notional <= 1% del dollar volume medio a 5 giorni
```

Se la size teorica supera il limite, il backtest deve troncare la size o saltare il trade.

### Overnight/catalyst risk

Small-cap possono fare offering o news after-hours. La strategia deve distinguere setup overnight-safe da setup da chiudere prima della sessione successiva.

## Benchmark corretti

Non usare solo SPY.

Benchmark minimi:

- IWM / Russell 2000 proxy;
- equal-weight universe return;
- random-entry baseline nello stesso universo;
- ticker buy-and-hold durante holding window;
- cash/flat baseline;
- cost-adjusted return.

## Label candidate

Da progettare dopo scanner e data audit:

- forward return 3/5/10 giorni;
- max favorable excursion prima di stop;
- target-before-stop con costi small-cap;
- close-above-entry-after-N-days;
- risk-adjusted forward return;
- ranking cross-sectional tra candidati giornalieri.

## Data quality requirements

`yfinance` puo' bastare solo per prototipo preliminare, ma non per conclusioni robuste.

Rischi:

- survivorship bias;
- delisted ticker mancanti;
- reverse split non affidabili;
- corporate actions incomplete;
- dati premarket/after-hours assenti;
- bid/ask assente;
- halt non modellati;
- offering/dilution non disponibili.

Provider da valutare in futuro:

- Polygon;
- Tiingo;
- Alpaca data;
- Nasdaq Data Link;
- Databento per intraday piu' serio.

## Prima milestone tecnica proposta

1. Creare universe builder small/mid-cap con filtri liquidita'.
2. Creare data-quality report per ticker candidati.
3. Creare scanner rule-based long-only senza ML.
4. Esportare candidati giornalieri e diagnostica.
5. Solo dopo, definire label e backtest dedicato.

## Regola di stop ricerca

Se un setup non supera costi conservativi, random baseline e benchmark small-cap coerente, non va ottimizzato ulteriormente.

Vedi [[Roadmap-Master]], [[Quant-Research-Priorities-2026-05-09]], [[2026-05-09-cascade-backtest-analysis]].
