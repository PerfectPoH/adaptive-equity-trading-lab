# Candidate 005 Recovery Breadth Backtest Postmortem 001

Decision: `CANDIDATE_005_ARCHIVE_CURRENT_FORM_RESEARCH_LEAD_ONLY`

Scope: review only. No additional backtest, no parameter sweep, no promotion.

## What Improved

- Breadth fixed the most embarrassing Candidate 004 failure mode: ex-best-symbol net is now positive.
- Trade count rose from 14 to 37.
- Win rate stayed above 50%.

## Why It Still Failed

- Top-symbol concentration is still `0.360`, above the 30% cap.
- Benchmark-relative net is negative versus IWM `-0.296672` and SPY `-0.324886`.
- Norgate trial history remains too short for promotion.

## Interpretation

Candidate 005 is the first version that actually reduces outlier dependency instead of merely hiding it. It is still not an alpha claim; it is a stronger research lead for a longer-history or benchmark-aware test.

## Next Allowed Action

`design_candidate_006_benchmark_aware_recovery_breadth_or_wait_for_long_history_data`
