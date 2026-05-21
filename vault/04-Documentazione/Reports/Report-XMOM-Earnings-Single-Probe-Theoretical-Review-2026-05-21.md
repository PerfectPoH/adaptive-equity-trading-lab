---
tipo: xmom-earnings-single-probe-theoretical-review
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: THEORETICAL_REVIEW_VALIDATED_NOT_APPROVED
---

# Report XMOM Earnings Single Probe Theoretical Review - 2026-05-21

## Scope

Recorded the theoretical provider/symbol review for the future one-provider, one-symbol earnings metadata probe.

The review selects:

```text
provider_candidate: Intrinio
symbol_candidate: CRMD
endpoint_candidate: expected_earnings_dates_or_equivalent
timestamp_field_candidate: expected_8k_at
```

This is not an approval. No live approval directory, output directory or trial ledger row was created.

No provider query, network call, market-data download, raw payload retention, extractor implementation, OOS execution, paper/live trading or strategy promotion was performed.

## Artifacts

```text
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/theoretical_review_manifest.json
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/provider_candidate_review.csv
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/timestamp_mapping_policy.csv
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/review_sources.csv
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/blocked_actions.csv
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/README.md
experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521/theoretical_review_validation_report.json
```

Validator:

```text
src/experiments/xmom_earnings_single_probe_theoretical_review_validator.py
tests/test_xmom_earnings_single_probe_theoretical_review_validator.py
```

## Result

```text
decision: XMOM_EARNINGS_SINGLE_PROBE_THEORETICAL_REVIEW_PASS
passed: 33
failed: 0
approval_granted: false
provider_query_performed: false
```

Targeted tests:

```text
7 passed
```

## Timestamp Mapping Policy

The future probe must only test whether the candidate timestamp can support this deterministic mapping:

```text
missing or midnight timestamp -> UNSPECIFIED -> purge
local time < 09:30 America/New_York -> BMO -> candidate
09:30 <= local time < 16:00 America/New_York -> DMT -> purge
local time >= 16:00 America/New_York -> AMC -> candidate, t0 next regular session
```

## Decision

The theoretical review is valid and non-executable.

Still blocked:

```text
create_live_approval_directory
create_output_directory
create_trial_ledger_entry
execute_probe
query_provider
save_raw_payload
implement_extractor
run_oos
paper/live
strategy_promotion
```

See [[Report-XMOM-Earnings-Single-Probe-Explicit-Approval-Template-2026-05-21]].
