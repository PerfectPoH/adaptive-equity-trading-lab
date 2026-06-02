# Candidate 004 Regime-Routed Portfolio Design 001

Candidate 004 is not a tuned rerun of Candidate 003. It is a new architecture created because Candidate 003 exposed useful portfolio evidence but failed robustness.

## Design Goal

Build a portfolio that has a sleeve for different market moments, but without letting the backtest choose regimes after the fact.

## Sleeve Set

- Momentum: allowed only in confirmed trend regimes.
- Mean Reversion: allowed only in range/recovery regimes.
- Defensive/Low-Vol: daily-compatible stabilizer replacing Dollar-Bar.
- Cash/No-Trade: explicit permission to do nothing in hostile regimes.

## Regime Router

The router classifies market days using frozen SPY/IWM daily features: trend state, volatility state, drawdown stress, and recovery state. Each regime maps to allowed and blocked sleeves.

## Why This Avoids Overfitting

- The regime definitions are fixed before a Candidate 004 backtest.
- The router decides sleeve eligibility, not optimized weights.
- Candidate 003 evidence motivates the architecture but does not set thresholds.
- Any Candidate 004 run remains trial-limited and non-promotable until full-history validation exists.

## Next Step

`create_candidate_004_regime_attribution_gate`