# Report Outlier-Resistant Diagnostic Harness - 2026-05-21

Decision: `OUTLIER_DIAGNOSTIC_COMPLETE_NO_EXECUTION`

## Scope

Diagnostic-only analysis of existing trade-log artifacts. No new provider query, market-data download, backtest, paper/live trading or strategy promotion was performed.

## Ranking

- DX-PROVIDER-REPLAY score=25 verdict=NEGATIVE_TOTAL_PNL_NO_PROMOTION trades=27 total_pnl=-1102.975928 median_pnl=221.611767 pnl_ex_top3=-8543.440707
- DX-RANKEX-001 score=20 verdict=NEGATIVE_MEDIAN_TRADE_NO_PROMOTION trades=100 total_pnl=5616.493401 median_pnl=-40.525014 pnl_ex_top3=-6282.544893
- DX-OOS-2025-RISK score=20 verdict=NEGATIVE_MEDIAN_TRADE_NO_PROMOTION trades=30 total_pnl=923.824159 median_pnl=-85.951743 pnl_ex_top3=-6973.981447
- DX-XMOM-001 score=5 verdict=NEGATIVE_MEDIAN_TRADE_NO_PROMOTION trades=11 total_pnl=109363.252898 median_pnl=-1232.395461 pnl_ex_top3=-50085.318842

## Interpretation

The harness prioritizes median trade quality and positive PnL after removing the top three winners. It is designed to make outlier-dependent ideas fail before they receive any new execution budget.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
