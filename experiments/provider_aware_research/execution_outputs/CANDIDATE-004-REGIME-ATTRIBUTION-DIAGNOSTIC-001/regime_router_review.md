# Candidate 004 Regime Router Review 001

Decision: `CANDIDATE_004_ROUTER_REVIEW_COMPLETE_BACKTEST_GATE_NOT_YET_APPROVED`

This review interprets the attribution diagnostic only. It does not authorize or perform a Candidate 004 backtest.

## Findings

- DRAWDOWN_STRESS is structurally hostile: 12 trades, weighted net -0.318338, win rate 8.3%. Candidate 004 should route active sleeves to Cash there.
- RECOVERY_BOUNCE is the only observed regime with a usable sample and positive distribution: 22 trades, weighted net 0.304517, win rate 59.1%.
- Momentum in RECOVERY_BOUNCE is the cleanest sleeve/regime cell: 16 trades, weighted net 0.285995, win rate 62.5%.
- TREND_UP_HIGH_VOL is positive but fragile: 8 trades, weighted net 0.346071, median net negative, win rate 37.5%, best symbol TERN-202605.
- RISK_OFF looks positive only because of 3 trades, so it must not override the ex-ante Cash rule.
- INSUFFICIENT_HISTORY must route to Cash because it produced 9 trades, weighted net -0.193473, win rate 0%.

## Router Draft

- DRAWDOWN_STRESS: `Cash/No-Trade` - negative net and near-total loss rate.
- INSUFFICIENT_HISTORY: `Cash/No-Trade` - no stable regime evidence.
- RECOVERY_BOUNCE: `Momentum primary; Mean Reversion diagnostic secondary` - only positive cell with enough mapped trades.
- TREND_UP_HIGH_VOL: `Momentum capped or confirmation-required only` - positive total but weak distribution.
- TREND_UP_LOW_VOL: `Diagnostic only until more trades` - only 6 trades total.
- RANGE_LOW_VOL: `Cash/No-Trade until evidence exists` - only 1 mapped trade.
- RANGE_HIGH_VOL: `Cash/No-Trade` - no mapped evidence.
- RISK_OFF: `Cash/No-Trade despite positive sample` - sample too small and ex-ante risk-off rule dominates.

## Next Allowed Action

`create_candidate_004_regime_routed_backtest_gate_if_user_approves`
