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
- esclusione opzionale ADR e biotech troppo binarie nella prima versione;
- esclusione o flag severo per ticker con reverse split frequenti, delisting risk o storico dati incompleto.

## Market regime filter obbligatorio

I setup small-cap non vanno valutati senza regime di mercato. Panic reversal, breakout e post-gap drift cambiano comportamento in modo radicale tra bull market, bear market e stress regime.

Feature/regole candidate:

- IWM sopra/sotto EMA 50;
- IWM sopra/sotto EMA 200;
- VIX in range accettabile;
- breadth di mercato small-cap se disponibile;
- regime SPY/IWM relativo;
- analisi separata dei risultati per regime.

Regole operative iniziali:

```text
Se IWM < EMA 50: scanner gira, ma non genera segnali operativi.
Se VIX > 35: tutti i trade vengono bloccati.
Se dati regime mancanti: no-trade, non fallback ottimistico.
```

Il backtest non deve mescolare 2020-2024 come un unico ambiente omogeneo senza report per regime.

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
- skip trade se gap di apertura supera 8-10% rispetto al close del segnale;
- valutare entry MOC o next-day limit logic;
- no fill se volume/dollar volume insufficiente;
- max position size vincolata alla liquidita'.

## Risk controls obbligatori

### Fail-closed

Regola fondativa: in caso di dati mancanti, ambiguita' di execution, regime non verificabile, liquidita' insufficiente o cash non disponibile, il sistema deve scartare il trade.

Lo scarto deve essere tracciato con una reason leggibile. Non sono ammessi fallback ottimistici.

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

### Float e short interest data limits

I dati sul float non sono affidabili su `yfinance`. Per squeeze participation e volume anomalo, il float e' una variabile critica ma difficile da automatizzare gratis.

Fonti candidate:

- Finviz per screening manuale;
- Nasdaq website per float ufficiale/manual check;
- provider API a pagamento o semi-gratuiti per automazione.

Lo short interest non viene usato nella prima fase. I dati FINRA arrivano con ritardo e non bastano per simulare squeeze in tempo reale. Ogni setup squeeze iniziale deve essere long-only e basato su volume/price action, non su short-interest storico ritardato.

### Capacity constraint

Regola proposta:

```text
position_notional <= 1% del dollar volume medio a 5 giorni
```

Se la size teorica supera il limite, il backtest deve troncare la size o saltare il trade.

### Overnight/catalyst risk

Small-cap possono fare offering o news after-hours. La strategia deve distinguere setup overnight-safe da setup da chiudere prima della sessione successiva.

### Outlier risk sui rendimenti

Le small-cap possono produrre equity curve apparentemente eccellenti grazie a pochi trade esplosivi. Un sistema non va promosso se il rendimento dipende da una manciata di outlier.

Metriche obbligatorie post-run:

```text
top_1_pnl_contribution_pct
top_3_pnl_contribution_pct
top_5_pnl_contribution_pct
top_10_pnl_contribution_pct
max_single_trade_contribution_pct
outlier_concentration_alert
```

Soglia iniziale proposta:

```text
top_3_pnl_contribution_pct > 0.40 => alert
```

### Monotonicita' dello scanner score

Il portfolio backtester fa triage dei candidati usando `small_cap_scanner_score`. Questa scelta e' valida solo se il punteggio e' monotono rispetto alla performance realizzata.

Il report post-run deve raggruppare i trade per decili di score e calcolare:

```text
trade_count
avg_return_pct
median_return_pct
win_rate
total_pnl
avg_pnl
simple_trade_sharpe
```

Se i decili alti non migliorano rispetto ai decili bassi, lo score resta diagnostico e non va usato per allocation, sizing o filtri live.

### Gate prima di nuovi vincoli portfolio

Non introdurre penalizzazioni settoriali, factor caps, random delay, survivorship sensitivity o opening regime check prima di misurare:

```text
raw portfolio_return
raw outlier concentration
raw score monotonicity
raw rejection_summary
```

Prima si misura la qualita' del segnale grezzo, poi si aggiungono controlli di diversificazione e realismo.

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

- survivorship bias, molto piu' grave che sulle large-cap;
- delisted ticker mancanti;
- reverse split non affidabili;
- corporate actions incomplete;
- dati premarket/after-hours assenti;
- bid/ask assente;
- halt non modellati;
- offering/dilution non disponibili.

Provider da valutare in futuro:

- Tiingo;
- Polygon;
- Alpaca data;
- Nasdaq Data Link;
- Databento per intraday piu' serio.

Step intermedio consigliato: valutare Tiingo prima di passare a provider piu' costosi, per migliorare affidabilita' small-cap rispetto a `yfinance`.

## Risorse research

- SSRN: cercare `small cap momentum`, `reversal anomaly`, `post-earnings drift small cap`.
- Alpha Architect: sintesi leggibili di paper quantitativi.
- Ernie Chan, `Quantitative Trading` e `Algorithmic Trading`.
- Marcos Lopez de Prado, `Advances in Financial Machine Learning`.

## Prima milestone tecnica proposta

1. Creare universe builder small/mid-cap con filtri liquidita'.
2. Creare data-quality report per ticker candidati.
3. Creare scanner rule-based long-only senza ML.
4. Esportare candidati giornalieri e diagnostica.
5. Solo dopo, definire label e backtest dedicato.

## Milestone tecnica corrente

Il portfolio backtester e' integrato nel runner storico. Il prossimo blocco deve essere il `Portfolio Diagnostics Report`:

```text
portfolio_outlier_breakdown.csv
portfolio_score_profile.csv
markdown sections:
- Portfolio Outlier Breakdown
- Score Profile Report
```

Questa milestone e' bloccante prima di nuovi affinamenti architetturali.

## Regola di stop ricerca

Se un setup non supera costi conservativi, random baseline, benchmark small-cap coerente, outlier concentration gate e score monotonicity gate, non va ottimizzato ulteriormente.

Vedi [[Roadmap-Master]], [[Quant-Research-Priorities-2026-05-09]], [[2026-05-09-cascade-backtest-analysis]], [[2026-05-10-cascade-small-cap-critical-diagnostics-roadmap]].
