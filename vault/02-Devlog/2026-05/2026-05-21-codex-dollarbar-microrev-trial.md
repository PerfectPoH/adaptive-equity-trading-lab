# Report DollarBar MicroRev Trial - 2026-05-21

Decision: `DOLLARBAR_MICROREV_ARCHIVE_CURRENT_FORM`

## Five-Step Run

- 1_static_dollarbar_data_layer_contract: STATIC_DOLLARBAR_DATA_LAYER_CANONICAL
- 2_ema_transform_blocked: EMA_DOLLARBAR_TRANSFORM_REJECTED_AND_BLOCKED
- 3_microrev_preregistration: PREREGISTERED_EXISTING_PANEL_ONLY
- 4_static_dollarbar_microrev_probe: evaluated_existing_panel
- 5_final_decision: NO_PROMOTION

## Result

- Evaluated files: 12
- Trades: 140
- Gross return sum: -0.8469489896
- Net return sum after 500 bps: -7.8469489896
- Positive net trade rate: 0.0
- Promotion blockers: net_return_not_positive_after_500bps, positive_net_trade_rate_below_50pct

## Panel

- AEHR_2023-03-02 AEHR trades=23 gross=-0.0087283086 net=-1.1587283086
- AEHR_2025-04-07 AEHR trades=20 gross=-0.1899167717 net=-1.1899167717
- ARRY_2024-11-06 ARRY trades=19 gross=-0.1814420933 net=-1.1314420933
- CABA_2022-04-04 CABA trades=1 gross=0.0047619048 net=-0.0452380952
- CABA_2022-06-21 CABA trades=3 gross=0.0 net=-0.15
- CABA_2022-06-23 CABA trades=2 gross=0.0200875857 net=-0.0799124143
- CABA_2022-07-28 CABA trades=4 gross=-0.0151578676 net=-0.2151578676
- CABA_2025-06-11 CABA trades=17 gross=-0.1135201279 net=-0.9635201279
- CABA_2025-09-18 CABA trades=7 gross=-0.0226848946 net=-0.3726848946
- CRMD_2024-03-12 CRMD trades=8 gross=-0.1668707427 net=-0.5668707427
- IOVA_2022-11-18 IOVA trades=15 gross=-0.1296511996 net=-0.8796511996
- IOVA_2025-04-07 IOVA trades=21 gross=-0.0438264741 net=-1.0938264741

## Interpretation

Static dollar-bars remain a canonical data-layer representation, but this micro-reversion rule is not promoted. The run used only existing intraday artifacts and did not query providers, sweep parameters, paper trade, live trade, or promote a strategy.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
