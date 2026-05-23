# Report SEC8K Tape Oracle Existing Intraday Backtest - 2026-05-22

Decision: `SEC8K_TAPE_ORACLE_ARCHIVE_CURRENT_EXISTING_DATA_FORM`

## Scope

Bounded backtest on existing intraday artifacts only. No provider query, market-data download, parameter sweep, paper/live trading, or promotion occurred.

## Result

- Evaluated SEC8K event count: 30
- Positive oracle trade count: 4
- Gross return sum: 0.0505549675
- Net return sum after 500 bps: -0.1494450325
- Blockers: positive_oracle_trade_count_below_30

## Panel

- AEHR 2022-04-01: status=evaluated, first15_return=-0.023364486, volume_ratio=5.587537, positive_oracle=False, net=0.0
- AEHR 2022-10-07: status=evaluated, first15_return=0.0735989196, volume_ratio=14.001208, positive_oracle=True, net=-0.0051243178
- AEHR 2023-01-06: status=evaluated, first15_return=0.0470980019, volume_ratio=11.313359, positive_oracle=True, net=-0.0486766652
- AEHR 2023-03-31: status=evaluated, first15_return=-0.0493716338, volume_ratio=9.134998, positive_oracle=False, net=0.0
- ARRY 2022-04-06: status=evaluated, first15_return=-0.0976594027, volume_ratio=5.69096, positive_oracle=False, net=0.0
- ARRY 2022-05-11: status=evaluated, first15_return=0.145631068, volume_ratio=1.941103, positive_oracle=False, net=0.0
- ARRY 2022-08-10: status=evaluated, first15_return=-0.0114231318, volume_ratio=2.058851, positive_oracle=False, net=0.0
- ARRY 2022-11-09: status=evaluated, first15_return=-0.0297997069, volume_ratio=8.014508, positive_oracle=False, net=0.0
- ARRY 2023-03-02: status=evaluated, first15_return=-0.0111761575, volume_ratio=2.97122, positive_oracle=False, net=0.0
- ARRY 2023-03-22: status=evaluated, first15_return=0.0105042017, volume_ratio=1.621964, positive_oracle=False, net=0.0
- ARRY 2023-05-10: status=evaluated, first15_return=0.0115321252, volume_ratio=4.849611, positive_oracle=True, net=-0.0475845411
- CABA 2022-03-17: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CABA 2022-05-12: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CABA 2022-08-11: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CABA 2022-11-10: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CABA 2023-03-16: status=evaluated, first15_return=-0.0547752809, volume_ratio=5.581135, positive_oracle=False, net=0.0
- CABA 2023-05-11: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CRMD 2022-03-30: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CRMD 2022-05-13: status=evaluated, first15_return=0.0341614907, volume_ratio=1.205124, positive_oracle=False, net=0.0
- CRMD 2022-08-11: status=evaluated, first15_return=0.027607362, volume_ratio=1.964374, positive_oracle=False, net=0.0
- CRMD 2022-11-10: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CRMD 2023-03-30: status=purged_incomplete_intraday_window, first15_return=, volume_ratio=, positive_oracle=False, net=0.0
- CRMD 2023-05-16: status=evaluated, first15_return=-0.0181451613, volume_ratio=3.910443, positive_oracle=False, net=0.0
- IOVA 2022-02-25: status=evaluated, first15_return=0.0853916725, volume_ratio=3.617386, positive_oracle=True, net=-0.0480595084
- IOVA 2022-05-06: status=evaluated, first15_return=-0.0211978466, volume_ratio=1.976229, positive_oracle=False, net=0.0
- IOVA 2022-08-05: status=evaluated, first15_return=0.0231759657, volume_ratio=2.131616, positive_oracle=False, net=0.0
- IOVA 2022-11-04: status=evaluated, first15_return=-0.012195122, volume_ratio=1.926458, positive_oracle=False, net=0.0
- IOVA 2023-03-01: status=evaluated, first15_return=0.031420765, volume_ratio=2.424864, positive_oracle=False, net=0.0
- IOVA 2023-05-10: status=evaluated, first15_return=-0.0052493438, volume_ratio=2.142048, positive_oracle=False, net=0.0
- IOVA 2023-07-11: status=evaluated, first15_return=-0.0114795918, volume_ratio=15.146319, positive_oracle=False, net=0.0

## Interpretation

The existing intraday archive contains too few SEC8K-matching events for promotion. Sample expansion requires a separate provider approval gate.
