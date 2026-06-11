---
tipo: feature-spec
progetto: adaptive-equity-trading-lab
stato: spec-congelata-non-implementata
data: 2026-06-11
ultimo-aggiornamento: 2026-06-11
tags: [true-backtest, etf, large-cap, capital-aware, spec, preregistrazione]
---

# TRIAL-TRUE-ETF-001 - True backtest su universo ammissibile (SPEC)

> Spec-only. Congelata prima dell'implementazione. Qualsiasi deviazione va
> dichiarata come emendamento nel vault PRIMA di eseguire.

## Obiettivo

Portare il "portfolio della casa" ([[Report-House-Portfolio-Trial-2026-06-11]])
da stream proxy a un backtest capital-aware su dati reali ammissibili,
SENZA bundle a pagamento.

## Universo (ammissibile con dati gratuiti)

- ETF: SPY, QQQ, IWM, settoriali SPDR (XLF, XLK, XLE, XLV, XLI, XLP, XLU, XLY, XLB).
- Large-cap correnti del panel storico del lab (AAPL, MSFT, NVDA, AMD, TSLA,
  META, AMZN, GOOGL).
- Razionale ammissibilita': survivorship bias strutturalmente minimo (ETF non
  delistano; le large-cap correnti hanno storia continua nel periodo testato).
  Limite dichiarato: resta un universo "comodo", non point-in-time puro.

## Componenti

Reimplementare come regole eseguibili i 4 template vincitori della ricetta
congelata: Momentum 90d/180d, Mean Reversion 180d, Dollar-Bar Microstructure
180d (versione daily-bar proxy). Ogni regola: segnale al close, entry al next
open, stop/timeout espliciti, costi 10 bps round-trip + slippage dichiarato.

## Motore

`run_small_cap_portfolio_backtest` (gia' esistente, cash accounting reale)
adattato all'universo ETF/large-cap: risk-based sizing 1% per trade, max
posizioni concorrenti 10, cash constraint reale, nessuna leva, no short.
Overlay difensivo: index regime classifier (HIGH_VOL 0.25 / TREND_DOWN 0.50).

## Split temporale preregistrato

- Selezione/parametri: SOLO 2018-2023 (gia' congelati dalla ricetta, nessun re-tuning).
- OOS primario: 2024-01 -> ultimo dato disponibile.
- Nessun parametro modificabile dopo il primo run OOS.

## Gate (tutte obbligatorie)

1. OOS positivo e batte buy-and-hold SPY su return/maxDD.
2. Ex-top3 trade: nessun sign flip.
3. DSR pass con trial_count dichiarato (=2: questa spec e' UNA combinazione).
4. N >= 100 trade OOS (vincolo di potenza dalla power curve PCTRL).
5. Costi/slippage: risultato positivo anche con costi raddoppiati.

## Cosa NON autorizza questa spec

Nessuna promozione automatica, nessun paper/live trading, nessuno sweep di
parametri, nessun provider a pagamento. Il download yfinance per ETF/large-cap
correnti e' ammesso previa conferma owner al momento dell'esecuzione.

Vedi [[Stato-Corrente]], [[Roadmap-Master]], [[Regole-Quant]].

---

## Emendamento 001 (2026-06-11, PRIMA dell'esecuzione)

Dichiarato prima di qualsiasi run OOS, come richiesto da questa spec:

1. **Regole causali al posto del ranking ex-post.** Le entry factory usavano
   ranking del segnale sull'intera storia (soglia nota ex-post). Il true
   backtest usa soglie ROLLING causali (quantile su finestra 252d trailing):
   - Momentum 90/180: entra se il 21d trailing return >= quantile rolling 0.90.
   - Mean Reversion 180: entra se il 2d return <= quantile rolling 0.10.
   - Dollar-Bar 180 (proxy daily): entra se il pct-change del dollar volume
     >= quantile rolling 0.90 in un giorno negativo.
2. **Motore dedicato** con gli stessi invarianti del backtester small-cap
   (entry next-open, cash reale, no leva) invece dell'adapter: meno rischio
   di comportamenti ereditati non pertinenti all'universo ETF.
3. **Costi 100 bps round-trip** (come le varianti factory vincitrici),
   PIU' conservativi dei 10 bps della spec originale.
4. **Exit solo a timeout** (fedele alle regole validate: la factory non ha stop).
5. **Sizing**: 10% dell'equity per posizione, max 10 concorrenti, no leva.
6. **Difesa**: exposure scaling del regime classifier all'entry
   (HIGH_VOL 0.25, TREND_DOWN 0.50). Il routing per-regime delle famiglie
   NON e' incluso in v1 (label set diverso); dichiarato come limite.
7. **Dati**: yfinance auto-adjusted, download autorizzato dall'owner in chat
   il 2026-06-11. Universo: SPY QQQ IWM + 9 settoriali SPDR + 8 large-cap correnti.
