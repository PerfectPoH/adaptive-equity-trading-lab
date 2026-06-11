# Report SEC8K Direction Tape Oracle Preregistration - 2026-05-22

Decision: `SEC8K_DIRECTION_TAPE_ORACLE_PREREGISTRATION_PASS`

## Scope

Created `PREREG-SEC8K-DIRECTION-001` / `TRIAL-SEC8K-DIRECTION-001` as a spec-only direction-source study for the SEC 8-K Item 2.02 regime candidate. This is not a strategy execution and does not authorize provider queries, intraday downloads, backtests, parameter sweeps, paper/live trading, or promotion.

## Frozen Hypothesis

The trial will test whether a long-only positive oracle derived from the first 15 minutes of RTH tape can identify continuation candidates on SEC 8-K Item 2.02 reaction sessions.

- Oracle window: `09:30-09:45 America/New_York`
- Hypothetical entry: `09:46 America/New_York`
- Exit policy: `same_day_flat_by_15:55`
- Candidate side: `long_only_positive_oracle`
- Volume ratio threshold: `3.0`
- Cost model: `500` bps
- DSR threshold: `0.95`
- Minimum trade count for promotion: `30`

## Guardrails

- No thresholds selected from XMOM PnL.
- XMOM/SEC8K overlap is historical interpretation only.
- Future returns, post-entry returns, realized PnL, and gap-fill outcomes are blocked as features.
- Negative oracle labels do not authorize short selling.
- Execution remains blocked until a separate intraday data-contract gate, explicit run authorization, and post-run statistical gate exist.

## Validation

Validator: `src.experiments.sec8k_direction_tape_oracle_preregistration_validator`

Result: `51/51` checks passed.

Targeted tests: `5/5` passed.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
