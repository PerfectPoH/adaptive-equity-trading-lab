# Report Amihud Liquidity Toxicity Diagnostic - 2026-05-22

Decision: `LIQUIDITY_TOXICITY_DIAGNOSTIC_ARCHIVE_CURRENT_FORM`

## Scope

Diagnostic-only Amihud illiquidity analysis on existing XMOM trade and Databento daily price artifacts. No provider query, market-data download, new backtest, parameter sweep, paper/live trading or promotion was performed.

## Result

- Trade count: 11
- High-ILLIQ loser rate: 0.333333
- Low-ILLIQ loser rate: 0.8
- Loser-rate separation: -0.466667
- High-ILLIQ median PnL: 37896.174002
- Low-ILLIQ median PnL: -9846.473523
- Blockers: trade_count_below_30, insufficient_loser_rate_separation, high_illiq_median_pnl_not_worse

## Panel

- CRMD 2024-12-31 bucket=high_illiq amihud=1.200041e-08 pnl=29862.620437 label=winner
- CRMD 2025-01-31 bucket=high_illiq amihud=8.08089e-09 pnl=-1232.395461 label=loser
- CRMD 2025-02-28 bucket=high_illiq amihud=1.106318e-08 pnl=-52688.381603 label=loser
- CRMD 2025-03-31 bucket=high_illiq amihud=1.122484e-08 pnl=45929.727566 label=winner
- CRMD 2025-04-30 bucket=high_illiq amihud=1.016963e-08 pnl=46861.703373 label=winner
- CRMD 2025-05-30 bucket=low_illiq amihud=4.60403e-09 pnl=-7703.904097 label=loser
- CRMD 2025-06-30 bucket=low_illiq amihud=5.14763e-09 pnl=-9846.473523 label=loser
- CRMD 2025-07-31 bucket=low_illiq amihud=2.59898e-09 pnl=39286.661902 label=winner
- AEHR 2025-08-29 bucket=high_illiq amihud=8.65218e-09 pnl=66657.140802 label=winner
- AEHR 2025-09-30 bucket=low_illiq amihud=3.40261e-09 pnl=-35910.761711 label=loser
- AEHR 2025-10-31 bucket=low_illiq amihud=5.93648e-09 pnl=-11852.684787 label=loser

## Interpretation

This diagnostic asks whether pre-entry Amihud illiquidity separates toxic trades from survivors. A positive diagnostic would still require a separate preregistration before any filter or strategy run.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
