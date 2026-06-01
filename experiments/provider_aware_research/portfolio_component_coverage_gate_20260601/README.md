# Portfolio Component Coverage Gate 001

This gate prevents Portfolio Candidate 002 from being falsely archived as a complete four-sleeve portfolio when only two sleeves are observable with Norgate daily data.

Norgate Data is admissible for survivor-aware daily OHLCV research, active and delisted equities, quote-date metadata, and historical constituent checks. It is not sufficient by itself for point-in-time catalyst direction or intraday dollar-bar/order-flow reconstruction.

The Norgate tradability rerun therefore falsifies the daily-compatible subset only:

- Momentum
- Mean Reversion

It does not fully falsify:

- Catalyst
- Dollar-Bar Microstructure

Candidate 002 remains unpromoted and blocked until all component data contracts are satisfied by separate provider gates.

## Provider conclusion

Norgate is the correct trial source for the daily survivor-aware sleeves, especially because it exposes active and delisted equities during the trial. It is not a complete one-provider solution for the whole portfolio.

The full candidate requires a provider stack:

- Daily survivor-aware equity history: Norgate or CRSP.
- Intraday trades/quotes/order book: Databento, NYSE TAQ, WRDS TAQ, or Nasdaq TotalView/ITCH.
- Earnings direction: I/B/E/S, FactSet PIT Estimates, Zacks/Sharadar/Quandl-equivalent paid feeds, or similar point-in-time consensus data.
- Biotech catalyst direction: BioMedTracker/Citeline/Evaluate-style clinical catalyst datasets, plus SEC/company-release audit trails.

Until those missing contracts exist, disabled sleeves must keep their frozen zero coverage label. The portfolio may not redistribute their weight and then claim the four-sleeve design was tested.
