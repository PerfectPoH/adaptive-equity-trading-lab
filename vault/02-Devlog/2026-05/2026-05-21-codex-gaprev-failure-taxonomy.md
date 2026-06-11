# Report GAPREV Failure Taxonomy - 2026-05-21

Decision: GAPREV_ARCHIVE_CURRENT_FORM

## Summary
- Events classified: 12
- Trades generated: 5
- No-trade events: 7
- Gross return sum on traded events: 0.1373459226119359
- Net return sum after 500 bps: -0.11265407738806399
- Positive net trades: 2
- Primary failure mode: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP

## Category Counts
- ADVERSE_CONTINUATION_OR_WEAK_REVERSION: 2
- GROSS_EDGE_COST_DESTROYED: 1
- NET_WIN_UNPROMOTABLE_SINGLE_EVENT: 2
- RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP: 6
- RTH_VOLUME_FILTER_FAIL: 1

## Interpretation
GapRev in its current form is archived. Most candidates selected from daily gaps do not remain valid RTH GapRev trades after intraday reconstruction, and the traded subset is net negative under the mandatory 500 bps stress cost. This is a structural failure, not a parameter-tuning invitation.

## Event Table
- AEHR 2023-03-02: GROSS_EDGE_COST_DESTROYED (trade_count=1, net_return=-0.0136490737504368)
- ARRY 2024-11-06: ADVERSE_CONTINUATION_OR_WEAK_REVERSION (trade_count=1, net_return=-0.0508077544426495)
- CABA 2025-06-11: ADVERSE_CONTINUATION_OR_WEAK_REVERSION (trade_count=1, net_return=-0.0871428571428571)
- CABA 2022-07-28: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- CRMD 2024-03-12: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- IOVA 2022-11-18: NET_WIN_UNPROMOTABLE_SINGLE_EVENT (trade_count=1, net_return=0.0381355932203389)
- AEHR 2025-04-07: NET_WIN_UNPROMOTABLE_SINGLE_EVENT (trade_count=1, net_return=0.0008100147275405)
- CABA 2022-06-21: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- CABA 2022-06-23: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- CABA 2025-09-18: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- CABA 2022-04-04: RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP (trade_count=0, net_return=nan)
- IOVA 2025-04-07: RTH_VOLUME_FILTER_FAIL (trade_count=0, net_return=nan)


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
