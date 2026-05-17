# 2026-05-17 - Data provider evaluation plan

## Contesto

Dopo la chiusura del programma NCTRL, il prossimo binario ammesso e' data/provider evaluation, non alpha sweep.

## Cosa e' stato fatto

Creato [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]].

La spec definisce criteri minimi per valutare provider/dataset small-cap su:

- point-in-time universe;
- delisted symbols;
- corporate actions;
- raw vs adjusted prices;
- halt/suspension awareness;
- volume integrity;
- licensing/storage;
- riproducibilita' API/snapshot.

## Stato

```text
SPEC ONLY / NOT EXECUTED
NO PROVIDER SELECTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Decisione

La valutazione provider e' un gate necessario ma non sufficiente per riaprire trial small-cap. Anche in caso di provider pass, servira' un successivo methodology gate su multiple testing, benchmark distribution, backtester audit e stop rules.
