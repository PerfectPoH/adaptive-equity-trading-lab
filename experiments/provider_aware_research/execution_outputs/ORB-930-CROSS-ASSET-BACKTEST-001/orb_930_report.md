# ORB-930-CROSS-ASSET-BACKTEST-001

## Verdict

- decision: `ORB_930_ARCHIVE_CURRENT_FORM`
- promotion_allowed: `False`
- blockers: `median_net_return_not_positive`
- total generated trades: `990`

## Best Configuration

- symbol: `BTC-USD`
- opening range: `5 minutes`
- reward multiple: `3R`
- trades: `59`
- win rate: `0.389831`
- net return sum: `0.02072309`
- median net return: `-0.00159155`

## Interpretation

The 9:30 AM opening-range breakout creates plenty of trades across gold, EUR/USD, and bitcoin, but the best configuration is still archived because the typical trade is negative after costs. The gross effect is not strong enough to become a governed candidate.

## Trade Counts By Symbol

- `BTC-USD`: `342`
- `EURUSD=X`: `351`
- `GC=F`: `297`

## Top Parameter Rows

| symbol | range_minutes | reward_r | trades | win_rate | gross_return_sum | net_return_sum | average_net_return | median_net_return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC-USD | 5 | 3 | 59 | 0.389831 | 0.05022309 | 0.02072309 | 0.00035124 | -0.00159155 |
| GC=F | 15 | 1 | 49 | 0.469388 | 0.0300109 | 0.0055109 | 0.00011247 | -0.00019762 |
| BTC-USD | 5 | 4 | 59 | 0.355932 | 0.03235163 | 0.00285163 | 4.833e-05 | -0.00179145 |
| GC=F | 5 | 1 | 50 | 0.48 | 0.01834314 | -0.00665686 | -0.00013314 | -0.00104507 |
| GC=F | 15 | 4 | 49 | 0.346939 | 0.0163542 | -0.0081458 | -0.00016624 | -0.00324231 |
| GC=F | 5 | 3 | 50 | 0.3 | 0.01466378 | -0.01033622 | -0.00020672 | -0.00338396 |
