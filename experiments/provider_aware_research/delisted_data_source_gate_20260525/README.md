# Delisted Data Source Gate 001

This gate answers one question: what data source is acceptable before the PDUFA 180-day investment-mode proxy can be tested as a real strategy?

It is not a provider probe, dataset download, backtest, parameter search, or promotion artifact. It blocks all execution and records the minimum data contract:

- survivor-bias-free historical common-stock universe,
- historical prices for delisted securities,
- listing and delisting dates,
- corporate action adjustments,
- point-in-time or reconstructable universe membership,
- biotech filtering metadata,
- a separate point-in-time PDUFA/FDA calendar before any event strategy run.

The current PDUFA workbench result remains `PROXY_INVESTMENT_CANDIDATE_ONLY`.

Admissible source families are CRSP, Norgate Data, and Sharadar/Nasdaq Data Link. Polygon/Massive remains `probe_required` because reference metadata is not enough; historical delisted price entitlement and PIT construction still need a separate approved probe.
