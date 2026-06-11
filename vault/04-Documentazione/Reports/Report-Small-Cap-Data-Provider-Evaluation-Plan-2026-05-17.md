---
tipo: evaluation-plan
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: SPEC_ONLY_NOT_EXECUTED
scope: data_provider_methodology_gate
---

# Report Small-Cap Data Provider Evaluation Plan - 2026-05-17

## Status

```text
SPEC ONLY / NOT EXECUTED
NO PROVIDER SELECTED
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document defines the next allowed data/methodology gate after the NCTRL program closure. It does not authorize any small-cap strategy trial.

## Background

The project has already established:

- `TRIAL-RANKEX-001` failed validation and is closed.
- The old small-cap breakout/open-to-close track is archived as non-promotable.
- The pre-registered data-quality audit concluded `NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE`.
- The NCTRL program is closed as `CLOSED / TECHNICAL PASS`, validating research machinery but not alpha.

Therefore, the next bottleneck is data quality and point-in-time methodology, not scanner tuning.

## Core question

```text
Can a candidate data provider support informative small-cap trials with point-in-time universes, delisted symbols, corporate actions, and halt/suspension awareness well enough to reopen small-cap research gates?
```

## Non-goals

- Do not select a trading strategy.
- Do not run a backtest.
- Do not optimize scanner thresholds.
- Do not preregister `TRIAL-XMOM-001`.
- Do not compare providers by marketing claims alone.
- Do not treat provider availability as proof of investible edge.

## Provider requirements

A provider candidate must be evaluated across these dimensions.

| Requirement | Description | Gate type |
|---|---|---|
| Point-in-time universe | Ability to reconstruct membership/eligibility as of historical dates, not today's surviving tickers | hard |
| Delisted symbols | Historical OHLCV remains accessible after delisting, bankruptcy, merger, ticker change, or suspension | hard |
| Corporate actions | Splits, reverse splits, dividends, special dividends, ticker changes, mergers, spin-offs and symbol changes are explicit and auditable | hard |
| Raw and adjusted prices | Both raw OHLCV and adjusted series are available or adjustment methodology is documented | hard |
| Halt/suspension representation | Halt/suspension/non-tradable periods are identifiable or at least not silently represented as liquid normal bars | hard |
| Volume integrity | Zero-volume, stale, corrected and missing-volume cases are explicit enough for warnings/gates | hard |
| Event metadata | Offerings/dilution/news are available directly or via compatible companion source | soft |
| API reproducibility | Queries are deterministic or snapshot-able with stable identifiers and timestamps | hard |
| Licensing | Research usage, storage and derived artifact retention are allowed | hard |
| Cost/limits | Cost and rate limits are feasible for repeated validation and bootstrap/random baseline work | soft |

## Minimum adversarial event panel

The provider must be tested on an adversarial panel selected before querying provider data.

Mandatory coverage:

| Category | Minimum cases | Required evidence |
|---|---:|---|
| Delisting/suspension/bankruptcy-like outcome | 2 | data remains retrievable or absence is explicit and documented |
| Reverse split | 2 | split ratio and raw/adjusted continuity are auditable |
| Trading halt/regulatory halt | 2 | halt/non-tradability is visible or externally joinable |
| Offering/dilution/ATM-like event | 2 | price/volume gap can be reconciled to event metadata or independent source |
| Special dividend/corporate action | 1 | action is explicit and adjustment is coherent |
| Ticker change/merger/name change | 1 | identifier continuity is preserved |

The previous yfinance audit cases can be reused as seed cases but must not be the whole panel:

- `TUP`
- `MULN`
- `CNGL`
- `ABAT`
- `WEYS`

The panel should be frozen in a separate audit-result document before provider queries are interpreted.

## Evaluation properties

For each provider and each event, assign the following fields.

| Field | Allowed values |
|---|---|
| `provider_symbol_resolves` | yes/no/partial |
| `historical_identifier_stable` | yes/no/partial |
| `event_window_available` | yes/no/partial |
| `raw_ohlcv_available` | yes/no |
| `adjusted_ohlcv_available` | yes/no |
| `corporate_action_metadata_available` | yes/no/partial/not_applicable |
| `halt_or_suspension_visible` | yes/no/partial/not_applicable |
| `delisted_history_available` | yes/no/not_applicable |
| `point_in_time_universe_supported` | yes/no/partial |
| `licensing_allows_research_storage` | yes/no/unclear |
| `pipeline_integration_complexity` | low/medium/high |
| `severity` | low/medium/high/critical |
| `verdict` | pass/caveat/fail |

## Provider-level scoring

Provider-level verdicts are predeclared as follows.

### `provider_usable_for_small_cap_trials`

Required:

```text
critical failures = 0
hard requirement failures = 0
>= 80% event rows pass or caveat
delisted symbols covered
reverse splits covered
point-in-time universe support yes or independently available through compatible dataset
license allows research storage/snapshots
```

This verdict does not open a trial directly. It allows drafting a future methodology-gate document.

### `provider_usable_with_caveats`

Allowed only if:

```text
critical failures = 0
hard requirement failures <= 1
>= 60% event rows pass or caveat
all caveats have explicit mitigation plan
no silent survivorship failure
license allows research storage/snapshots
```

This verdict permits only a caveated methodology plan, not strategy execution.

### `provider_not_usable`

Triggered by any of:

```text
critical failures >= 1
silent survivorship or delisting failure
no point-in-time universe path
no auditable corporate-action handling
license/storage unclear for reproducible research
< 60% event rows pass or caveat
```

With this verdict, no small-cap trial may be opened on that provider as primary evidence.

## Required outputs

A future execution of this plan must produce:

1. frozen event panel;
2. provider candidate list;
3. per-provider requirement table;
4. per-event provider audit table;
5. licensing/storage notes;
6. integration complexity notes;
7. final provider verdict;
8. explicit decision on whether a methodology gate can be drafted.

Suggested report name:

```text
Report-Small-Cap-Data-Provider-Evaluation-Result-YYYY-MM-DD.md
```

## Candidate provider classes

This plan intentionally does not pick a vendor. The evaluation should compare provider classes first:

| Class | Examples of capability to verify |
|---|---|
| Institutional equity data vendors | point-in-time fundamentals/universe, delisted history, corporate actions |
| Market-data APIs with corporate actions | raw/adjusted OHLCV plus split/dividend metadata |
| Exchange/official sources | halt/suspension notices, listing status, symbol changes |
| SEC/company-event sources | offerings, dilution, bankruptcy, merger, issuer events |
| Hybrid stack | price provider plus event/corporate-action provider plus local point-in-time snapshots |

Vendor names, pricing and current API claims should be researched fresh during execution, not assumed in this spec.

## Integration implications

If a provider passes, likely code changes will be required before any strategy trial:

- provider abstraction beyond `download_ticker`;
- explicit raw vs adjusted OHLCV schema;
- corporate-action event model;
- point-in-time universe snapshot format;
- delisted/ticker-change identifier mapping;
- provider provenance fields in `run_manifest.json`;
- data-quality checks that distinguish missing, suspended, delisted and non-tradable states;
- artifact retention policy compatible with license.

These changes should be implemented with TDD before any strategy backtest uses the new data.

## Stop rules

Stop the provider evaluation if any of the following occurs:

- provider license forbids local research artifact retention;
- delisted test symbols cannot be reconstructed;
- corporate-action adjustment method cannot be audited;
- point-in-time universe support is absent and no compatible independent universe source exists;
- provider query results cannot be reproduced or snapshotted.

## Governance after this plan

Current status remains:

```text
SMALL-CAP TRIALS: BLOCKED
YFINANCE DAILY ALONE: NOT USABLE AS PRIMARY EVIDENCE
NCTRL PROGRAM: CLOSED / TECHNICAL PASS
NEXT ALLOWED WORK: EXECUTE THIS PROVIDER EVALUATION OR HARDEN TOOLING
```

A passing provider evaluation is necessary but not sufficient to open a new small-cap trial. After provider evaluation, the project still needs a methodology gate covering multiple-testing ledger, benchmark distribution, backtester audit, and preregistered stop rules.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
