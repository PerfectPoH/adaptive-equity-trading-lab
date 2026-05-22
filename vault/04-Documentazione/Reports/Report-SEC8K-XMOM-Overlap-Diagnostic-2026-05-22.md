# Report SEC8K XMOM Overlap Diagnostic - 2026-05-22

Decision: `SEC8K_XMOM_OVERLAP_SUPPORTS_CATALYST_EXPLANATION`

## Scope

Diagnostic-only overlap between XMOM-001 trades and SEC 8-K Item 2.02 reaction-session windows. No provider query, new backtest, parameter sweep, paper/live trading or promotion was performed.

## Result

- Trade count: 11
- Window days: +/-5 trading days
- Overlap count: 8
- Overlap rate: 0.727273
- Winner overlap rate: 1.0
- Loser overlap rate: 0.5
- Top3 winner overlap rate: 1.0
- Overlap median PnL: 34574.641169
- Outside median PnL: -7703.904097
- Blockers: trade_count_below_30

## Panel

- CRMD signal=2024-12-31 pnl=29862.620437 overlap=True event=2025-01-07 anchor=entry dist=-3 top3=False
- CRMD signal=2025-01-31 pnl=-1232.395461 overlap=False event=2025-03-25 anchor=exit dist=-14 top3=False
- CRMD signal=2025-02-28 pnl=-52688.381603 overlap=True event=2025-03-25 anchor=exit dist=5 top3=False
- CRMD signal=2025-03-31 pnl=45929.727566 overlap=True event=2025-05-06 anchor=exit dist=-3 top3=True
- CRMD signal=2025-04-30 pnl=46861.703373 overlap=True event=2025-05-06 anchor=entry dist=-3 top3=True
- CRMD signal=2025-05-30 pnl=-7703.904097 overlap=False event=2025-05-06 anchor=signal dist=17 top3=False
- CRMD signal=2025-06-30 pnl=-9846.473523 overlap=True event=2025-08-07 anchor=exit dist=-5 top3=False
- CRMD signal=2025-07-31 pnl=39286.661902 overlap=True event=2025-08-07 anchor=entry dist=-4 top3=False
- AEHR signal=2025-08-29 pnl=66657.140802 overlap=True event=2025-10-07 anchor=exit dist=-4 top3=True
- AEHR signal=2025-09-30 pnl=-35910.761711 overlap=True event=2025-10-07 anchor=entry dist=-4 top3=False
- AEHR signal=2025-10-31 pnl=-11852.684787 overlap=False event=2025-10-07 anchor=signal dist=18 top3=False

## Interpretation

This diagnostic asks whether XMOM was accidentally exposed to SEC 8-K regimes. It is historical interpretation only and must not be used as a trading filter without a separate preregistration.
