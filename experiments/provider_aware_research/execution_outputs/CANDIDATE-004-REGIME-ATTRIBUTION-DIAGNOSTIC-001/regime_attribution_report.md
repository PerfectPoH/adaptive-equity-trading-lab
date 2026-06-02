# Candidate 004 Regime Attribution Diagnostic 001

Decision: `CANDIDATE_004_REGIME_ATTRIBUTION_COMPLETE_NO_BACKTEST`

Scope: attribution only. No Candidate 004 backtest, no parameter sweep, no promotion.

## Accounting

- Provider query performed: `True` (scope: SPY/IWM only).
- Market-data download performed: `False`.
- Portfolio backtest performed: `False`.
- Promotion allowed: `False`.

## Summary

- Mapped trades: `61`.
- Regime labels observed: `7`.

## Sleeve / Regime Actions

- Mean Reversion / DRAWDOWN_STRESS: trades=4 weighted_net=-0.145085 win_rate=0.250 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Mean Reversion / INSUFFICIENT_HISTORY: trades=3 weighted_net=-0.090444 win_rate=0.000 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Mean Reversion / RANGE_LOW_VOL: trades=1 weighted_net=-0.008050 win_rate=0.000 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Mean Reversion / RECOVERY_BOUNCE: trades=6 weighted_net=0.018522 win_rate=0.500 action=`CANDIDATE_ALLOWED_SLEEVE`
- Mean Reversion / RISK_OFF: trades=1 weighted_net=0.048871 win_rate=1.000 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Mean Reversion / TREND_UP_HIGH_VOL: trades=2 weighted_net=0.053182 win_rate=0.500 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Mean Reversion / TREND_UP_LOW_VOL: trades=2 weighted_net=-0.043710 win_rate=0.500 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Momentum / DRAWDOWN_STRESS: trades=8 weighted_net=-0.173253 win_rate=0.000 action=`BLOCK_OR_ROUTE_TO_CASH`
- Momentum / INSUFFICIENT_HISTORY: trades=6 weighted_net=-0.103029 win_rate=0.000 action=`BLOCK_OR_ROUTE_TO_CASH`
- Momentum / RECOVERY_BOUNCE: trades=16 weighted_net=0.285995 win_rate=0.625 action=`CANDIDATE_ALLOWED_SLEEVE`
- Momentum / RISK_OFF: trades=2 weighted_net=0.298969 win_rate=1.000 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`
- Momentum / TREND_UP_HIGH_VOL: trades=6 weighted_net=0.292889 win_rate=0.333 action=`POSITIVE_BUT_WEAK_DISTRIBUTION_REQUIRE_CAP_OR_CONFIRMATION`
- Momentum / TREND_UP_LOW_VOL: trades=4 weighted_net=0.055355 win_rate=0.500 action=`INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY`

## Next Step

`review_candidate_004_regime_attribution_before_backtest_gate`
