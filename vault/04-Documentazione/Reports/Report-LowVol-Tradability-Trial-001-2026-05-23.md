# Report LowVol Tradability Trial 001 - 2026-05-23

Decision: `LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM`

## Scope

Existing Databento daily OHLCV artifact only. No provider query, market-data download, intraday query, parameter sweep, short selling, paper/live trading, or promotion occurred.

## Result

- Trade count: 49
- Gross return sum: -0.4661574616
- Net return sum after 500 bps: -2.9161574616
- Median net return: -0.0779898219
- Net win rate: 0.22449
- Net return sum ex-top3: -3.8479231662
- Symbols traded: AEHR, ARRY, CRMD, IOVA
- Blockers: net_return_not_positive_after_500bps, median_net_return_not_positive

## Interpretation

This is a long-only low-volatility/tradability backtest, not a fundamental-quality strategy. It can only become a candidate if it survives the 500 bps cost model, sample-size gate, median-return gate and outlier-resistance gate.
