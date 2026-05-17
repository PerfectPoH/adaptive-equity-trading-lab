---
tipo: execution-checklist
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: CHECKLIST_READY_PROVIDER_QUERY_NOT_EXECUTED
scope: data_provider_methodology_gate
---

# Report Small-Cap Provider Evaluation Execution Checklist - 2026-05-17

## Status

```text
CHECKLIST READY
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO PRICING DECISION
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document converts [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]], [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]] and [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]] into an execution checklist.

It does not select a provider and does not authorize data downloads.

## Objective

Prepare a disciplined provider-evaluation execution pass that can answer:

```text
Can a candidate provider represent the frozen 10-event adversarial small-cap panel well enough to support future methodology-gated trials?
```

## Non-goals

- Do not run a trading strategy.
- Do not run a backtest.
- Do not run OOS, validation or ranking.
- Do not open `TRIAL-XMOM-001`.
- Do not choose a provider based on marketing pages alone.
- Do not spend money or enter a paid subscription without explicit approval.
- Do not treat a provider pass as investible edge.

## Candidate provider short-list for evaluation

This is a candidate list, not a selection.

| Provider | Current public/free-trial signal checked | Candidate role | Key unresolved checks before use |
|---|---|---|---|
| Databento | Public site advertises `$125` free credits and historical/real-time market data APIs | first candidate for usage-credit evaluation | confirm US equities historical dataset coverage for delisted/suspended small-cap symbols, corporate actions, raw vs adjusted data, licensing/snapshot retention, exact cost for frozen panel |
| Intrinio Starter Plan | Official guide says two-week free trial; includes active and delisted companies/securities; stock prices from 1967 active and 2007 delisted | strong candidate for delisted-history and corporate-action evaluation | confirm trial access includes required endpoints, license allows local research artifacts, API units sufficient for 10-event panel, raw/adjusted fields and point-in-time behavior |
| Massive / Polygon | Official pricing page redirects to Massive; Stocks Basic shows free plan, 5 API calls/minute, 2 years historical data, corporate actions/reference data available | limited free-tier sanity check, especially recent panel events | 2-year history may be insufficient for broader future audits; verify delisted symbol access, ticker-change behavior, and whether historical delisted coverage is complete |
| Tiingo | Public pages indicate EOD product; free-tier claims require direct account/pricing verification | possible low-cost secondary check | verify current free tier, delisted coverage, corporate actions, API limits, retention/license terms; do not assume delisted support |
| IEX Cloud | Current official free-plan claim not confirmed in this pass | hold / verify existence before considering | verify whether service/free tier still exists, current terms, historical depth, delisted coverage and licensing |
| Alpha Vantage | Known low free-call budget; not prioritized | fallback only for toy endpoint sanity | likely insufficient for frozen panel; must not be used as primary evidence |
| EODHD | Low free-call budget reported; not prioritized | fallback only for toy endpoint sanity | likely insufficient for frozen panel; verify delisted/corporate-action capabilities before any use |

## Source notes from this pass

- Databento pricing/search metadata confirms public claim of `$125` free credits and broad market-data API positioning.
- Intrinio official Starter Plan guide explicitly states two-week free trials and coverage of active/delisted companies and securities.
- Massive/Polygon official pricing content shows `Stocks Basic` as free with 5 API calls/minute, 2 years historical data, all US stock tickers, corporate actions and reference data available.
- Tiingo and IEX Cloud claims remain weaker or unconfirmed from official pages in this pass; they must be rechecked during execution.

## Pre-execution gating checklist

Before any provider query:

| Check | Required answer |
|---|---|
| Frozen panel loaded | `DPE-001..DPE-010` exactly as frozen |
| Provider candidate named | one provider at a time |
| Provider account type recorded | free credits / free tier / trial / paid |
| Credit-card/payment state recorded | yes/no and amount authorized |
| License reviewed | local research storage and derived artifact retention explicitly allowed or unclear |
| API terms captured | URL and date captured |
| Rate limits captured | yes |
| Query cost estimate captured | yes |
| Data retention policy captured | yes |
| Raw vs adjusted model understood | yes/partial/no |
| Corporate-action endpoint identified | yes/partial/no |
| Delisted-symbol behavior documented | yes/partial/no |
| Point-in-time universe path identified | yes/partial/no |
| Snapshot plan defined | yes |

If any hard item is `no`, stop before querying.

## Minimal query plan per provider

Run providers one at a time. Do not compare providers until each has a completed independent row set.

For each event `DPE-001..DPE-010`, collect:

1. **Identifier resolution**
   - Does the current API resolve the historical ticker?
   - Does it map old and new tickers where applicable?
   - Does it return delisted/suspended names?

2. **Historical OHLCV availability**
   - Raw OHLCV for event window.
   - Adjusted OHLCV for event window, if available.
   - Explicit missing-data response if unavailable.

3. **Corporate action/event metadata**
   - Splits/reverse splits.
   - Dividends/special dividends.
   - Ticker changes/business combinations.
   - Offering/dilution metadata, if available or joinable.

4. **Halt/suspension visibility**
   - Halt status endpoint or field.
   - Intraday gap/non-tradability evidence if available.
   - Daily zero-volume/stale-bar handling if no intraday data.

5. **Reproducibility**
   - Query URL or request parameters.
   - Timestamp.
   - Provider dataset/version if available.
   - Snapshot hash after local write.

## Required artifact layout for future execution

Suggested output root:

```text
experiments/provider_evaluations/<provider_slug>_event_panel_20260517/
```

Required files:

```text
provider_manifest.json
provider_requirement_table.csv
provider_event_audit_table.csv
license_notes.md
query_cost_estimate.md
raw_responses_manifest.csv
snapshot_hashes.csv
provider_evaluation_summary.md
```

No strategy artifacts should be produced in this directory.

## Provider manifest fields

`provider_manifest.json` must include:

| Field | Requirement |
|---|---|
| `provider_name` | provider legal/product name |
| `provider_slug` | stable lowercase slug |
| `account_type` | free_credits/free_tier/free_trial/paid |
| `payment_authorized` | true/false |
| `payment_cap_usd` | numeric, 0 if none |
| `execution_date` | ISO date |
| `operator` | human/operator name or local alias |
| `frozen_panel_report` | link to panel freeze report |
| `panel_expansion_report` | link to expansion report |
| `terms_url` | provider terms/pricing URL |
| `license_storage_verdict` | yes/no/unclear |
| `data_retention_allowed` | yes/no/unclear |
| `dataset_names` | list |
| `api_versions` | list |
| `query_budget_estimate_usd` | numeric or null |
| `actual_query_cost_usd` | numeric or null |
| `provider_query_executed` | true only after actual execution |

## Provider-event audit fields

`provider_event_audit_table.csv` must contain at least:

```text
event_id,provider_name,provider_symbol_resolves,historical_identifier_stable,event_window_available,raw_ohlcv_available,adjusted_ohlcv_available,corporate_action_metadata_available,halt_or_suspension_visible,delisted_history_available,point_in_time_universe_supported,licensing_allows_research_storage,pipeline_integration_complexity,severity,verdict,notes
```

## Provider-level verdict rules

Use the verdicts already defined in [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]].

### `provider_usable_for_small_cap_trials`

Allowed only if:

```text
critical failures = 0
hard requirement failures = 0
>= 80% event rows pass or caveat
delisted symbols covered
reverse splits covered
point-in-time universe support yes or independently available through compatible dataset
license allows research storage/snapshots
```

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

## Execution sequence recommendation

Recommended order if the user decides to execute later:

1. **Intrinio trial check**
   - Reason: official guide explicitly mentions delisted securities and two-week trial.
   - Stop if license/storage is incompatible.

2. **Databento credit check**
   - Reason: public `$125` credits and strong market-data API positioning.
   - Stop if delisted small-cap/corporate-action support is absent or cost estimate is unclear.

3. **Massive/Polygon free-tier sanity check**
   - Reason: free tier has limited but official query budget and recent history.
   - Treat as recent-event endpoint sanity, not full provider verdict unless delisted coverage is proven.

4. **Tiingo verification**
   - Reason: potentially useful low-cost EOD source, but free/delisted claims need direct confirmation.

5. **IEX Cloud verification only if still available**
   - Reason: current free-tier status not confirmed here.

This order is operational, not a ranking of quality.

## Stop rules

Stop immediately if:

- license forbids local storage/snapshots;
- account signup requires payment not explicitly approved;
- provider silently drops delisted symbols;
- provider cannot distinguish missing, delisted, suspended and normal zero-volume states;
- corporate-action adjustments are undocumented;
- query results are not reproducible or snapshot-able;
- provider coverage causes any attempt to replace frozen events.

## Governance consequence

This checklist makes the next provider-evaluation execution safer, but does not execute it.

Current status remains:

```text
SMALL-CAP TRIALS: BLOCKED
PROVIDER EVALUATION: CHECKLIST READY / NOT EXECUTED
PROVIDER EVENT PANEL: 10 EVENTS FROZEN
TRIAL-XMOM-001: NOT AUTHORIZED
```
