# Hypothesis

`TRIAL-SEC8K-DIRECTION-001` tests the following falsifiable hypothesis in a future separately authorized run:

> On SEC 8-K Item 2.02 reaction sessions, a long-only positive oracle derived from the first 15 minutes of RTH price and volume can identify continuation candidates whose intraday returns after 09:46 survive a 500 bps cost model and pass DSR >= 0.95.

The study is intentionally narrow. It does not infer earnings surprise magnitude from the close, from post-entry PnL, or from XMOM outcomes. It uses the early RTH tape as the only direction source available before a hypothetical entry. The candidate is invalid if the signal only works after lowering costs, changing the oracle window, changing the volume ratio threshold, allowing shorts, or reusing any XMOM-derived threshold.

Status remains `SPEC_ONLY_NOT_EXECUTED`. Execution remains blocked.
