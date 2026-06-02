# Norgate Candidate 003 Schema Probe 001

- decision: `NORGATE_CANDIDATE_003_SCHEMA_PROBE_PASS_TRIAL_LIMITED`
- linked candidate: `PORTFOLIO-CANDIDATE-003-MANUAL-COMPOSITE`
- package available: `True`
- package version: `1.0.74`
- active database available: `True`
- delisted database available: `True`
- active symbol sample: `A, AA, AAA, AAAA, AAAC`
- delisted symbol sample: `AACIU-202408, AACT.U-202509, AAM.U-202601, AAM-202602, AAN-202410`
- listing/delisting metadata available: `True`
- historical constituent watchlists available: `True`
- adjusted daily price function available: `True`
- previous delisted price accessibility evidence: `True`
- trial history limit: `2_years_expected_from_trial_terms`
- missing evidence: `none`

## Scope Discipline

This probe inspected Norgate package/schema/metadata availability for Candidate 003. It did not run the Candidate 003 portfolio backtest, did not calculate strategy returns, did not create an equity curve, and did not authorize paper or live trading.

## Next Step

If accepted, create a separate micro-backtest gate with bounded Norgate usage, frozen symbols/rules, no parameter sweep, and explicit trial-window limitations.