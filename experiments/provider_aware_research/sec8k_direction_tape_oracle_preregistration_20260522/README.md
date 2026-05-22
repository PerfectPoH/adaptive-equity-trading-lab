# PREREG-SEC8K-DIRECTION-001

Status: `SPEC_ONLY_NOT_EXECUTED`

Trial: `TRIAL-SEC8K-DIRECTION-001`

This preregistration defines a long-only positive oracle study for SEC 8-K Item 2.02 reaction sessions. The prior SEC 8-K diagnostics established a volatility and volume regime, and the XMOM overlap diagnostic supports historical catalyst exposure. This document does not authorize a backtest, parameter sweep, provider query, paper trading, live trading, or promotion.

The core question is whether the first full RTH tape response can act as a point-in-time direction source without reading future returns. The oracle window is fixed at 09:30-09:45 America/New_York. If the first 15-minute RTH return is positive and the first 15-minute volume ratio is at least 3.0 versus comparable control windows, a future implementation may label the event as `positive_oracle_candidate`. Negative or flat oracle labels are observation-only and do not authorize short selling.

No thresholds selected from XMOM PnL. The overlap diagnostic is only historical interpretation and may not be used as a trading filter. All execution remains blocked until a separate intraday data-contract gate, run authorization, and post-run statistical gate exist.
