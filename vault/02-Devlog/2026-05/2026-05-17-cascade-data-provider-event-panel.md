# 2026-05-17 - Data provider event panel

## Contesto

Dopo [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]], serviva congelare il pannello eventi prima di qualunque query o interpretazione provider.

## Cosa e' stato creato

Creato [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]].

Il documento congela:

- 5 seed event gia' selezionati da fonti indipendenti nel precedente audit yfinance: `TUP`, `MULN`, `CNGL`, `ABAT`, `WEYS`;
- 5 expansion slots obbligatori da riempire prima di esecuzione provider se si procede al panel completo;
- campi richiesti per ogni slot;
- regola: nessuna query provider prima del freeze.

## Stato

```text
EVENT PANEL FROZEN
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Governance

Il panel freeze riduce selection bias nella futura provider evaluation. Non autorizza `TRIAL-XMOM-001` e non cambia il blocco su yfinance daily alone.
