# 2026-05-17 - Data provider event panel expansion

## Contesto

Dopo il freeze iniziale del provider event panel, sono stati verificati i cinque expansion slots `DPE-006..DPE-010` con fonti pubbliche/issuer/exchange prima di qualunque query provider.

## Verifica

Eventi accettati:

- `FSR` - NYSE/ICE delisting proceedings and immediate suspension, 2024-03-25;
- `PHUN` - 1-for-50 reverse split, post-split trading 2024-02-27;
- `GH` - Nasdaq temporary trading halt pending FDA panel, 2024-05-23;
- `ICU` - $10M registered direct offering, 2024-07-10;
- `DWAC -> DJT` - ticker change/business combination, 2024-03-26.

Correzione:

- la proposta `CCB` luglio 2024 non e' stata congelata: le fonti trovate indicavano offerta dicembre 2024, non luglio. Sostituita con `ICU`, verificata su GlobeNewswire/issuer.

## Output

Creato [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]].

## Stato

```text
EXPANSION SLOTS FILLED
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

## Governance

Il pannello provider completo e' ora composto da 10 eventi avversariali. Questo consente una futura provider evaluation, ma non seleziona provider e non autorizza trial small-cap.
