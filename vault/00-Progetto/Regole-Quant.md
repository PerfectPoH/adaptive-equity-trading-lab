---
tipo: regole-quant
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [quant, backtest, risk, bias, ml]
---

# Regole Quant

## 1. Regola madre

Una pipeline che bara vale zero, anche se mostra performance alte. Un backtest onesto che perde e' piu' utile di un backtest bello ma contaminato.

## 2. Dati

- `yfinance` e' solo per MVP.
- Ogni snapshot deve avere hash.
- Dataset vuoti o troncati vanno scartati.
- Se un download fresco fallisce, usare solo snapshot locali gia' validati; non cambiare universo in modo silenzioso.
- Per live serio servono dati point-in-time e survivorship-bias-free.

## 3. Feature

- Ogni feature deve essere calcolabile conoscendo solo passato e presente.
- Rolling window solo backward-looking.
- Scaler fit solo su train.
- Se una feature dipende da SPY, SPY deve essere allineato temporalmente senza forward fill sospetto.

## 4. Label

```text
1 = take profit raggiunto prima dello stop loss entro N giorni
0 = stop loss prima, oppure timeout senza take profit
```

Timing:

```text
feature al close di oggi
segnale dopo il close
entry al next open
stop/take profit calcolati da entry effettiva
```

Se nella stessa candela vengono toccati stop e take profit, usare scelta conservativa: label 0.

Le label possono guardare avanti solo dentro lo stesso periodo temporale. Le ultime barre di train, validation e test vanno purgate se l'orizzonte della label supera il confine del periodo.

## 5. Split

```text
Train: 2020-2022
Validation: 2023
Test: 2024
Forward: 2025+
```

Vietato: random split, tuning su test, feature selection sul test, cambiare soglie dopo aver visto il test senza loggare.

Ogni scelta di soglia/modello va promossa solo se selezionata su validation o walk-forward, non perche' migliora direttamente il test 2024.

## 6. Execution

- Il trade entra al next open, non al close dello stesso giorno.
- Se gap overnight supera soglia massima, saltare il trade o loggare il caso.
- Simulare commissioni e slippage anche nell'MVP.
- Backtesting.py e' accettato solo come prototipo.

## 7. Risk MVP

```text
max 1% rischio per trade
max 3 posizioni
stop obbligatorio
no averaging down
no leva
no short
```

## 8. Metriche minime

- total return;
- max drawdown;
- win rate;
- profit factor;
- Sharpe;
- average win/loss;
- exposure time;
- buy-and-hold return;
- excess return;
- beats buy-and-hold.

## 9. Gate prima del live serio

Obbligatorio: dati point-in-time, survivorship-bias-free, event-driven backtester, Deflated Sharpe Ratio, CPCV, PBO, dynamic slippage, fiscalita' netta, slippage/paper-vs-live tracking.

Vedi [[Roadmap-Master]].
