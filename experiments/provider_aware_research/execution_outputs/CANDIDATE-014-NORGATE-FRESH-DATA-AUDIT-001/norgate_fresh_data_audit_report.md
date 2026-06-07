# Candidate 014 Norgate Fresh Data Audit

Decision: `CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_BLOCKED`

Scope: bounded local Norgate coverage audit only. No dataset build, no market-data download, no backtest, no Kronos inference, no portfolio selection, and no promotion.

## Coverage

- Active symbols available: `28187`
- Delisted symbols available: `1351`
- Loaded active sample: `485`
- Loaded delisted sample: `500`
- Loaded benchmarks: `2`
- Earliest first date: `2024-06-03`
- Latest last date: `2026-06-05`
- Max history years: `2.0041`
- Median history years: `1.3251`

## Blockers

- `history_span_below_5_years`
