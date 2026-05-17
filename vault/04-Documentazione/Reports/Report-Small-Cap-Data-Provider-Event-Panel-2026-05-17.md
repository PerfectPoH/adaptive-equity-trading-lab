---
tipo: event-panel-freeze
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: EVENT_PANEL_FROZEN_PROVIDER_QUERY_NOT_EXECUTED
scope: data_provider_methodology_gate
---

# Report Small-Cap Data Provider Event Panel - 2026-05-17

## Status

```text
EVENT PANEL FROZEN
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO PRICING DECISION
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document freezes the adversarial event panel to be used by the future data-provider evaluation defined in [[Report-Small-Cap-Data-Provider-Evaluation-Plan-2026-05-17]].

It does not evaluate any provider.

## Purpose

A provider evaluation can be biased if events are selected after seeing provider coverage, marketing claims, sample APIs or pricing tiers.

This document prevents that by freezing the event panel before any provider query is interpreted.

## Non-goals

- Do not select a data provider.
- Do not query provider APIs.
- Do not compare pricing.
- Do not run a strategy trial.
- Do not run a backtest, validation, OOS or sweep.
- Do not use this panel as alpha evidence.
- Do not reopen `TRIAL-XMOM-001`.

## Panel construction rule

The panel is split into:

1. **Frozen seed events** already selected from independent sources during the prior yfinance audit.
2. **Frozen expansion slots** that must be filled from independent sources before provider execution if a provider evaluation requires the full 10-case panel.

No provider-specific query may be used to choose or replace an event.

## Frozen seed events

| Event ID | Ticker | Event date | Category | Independent source basis | Window | Capability tested |
|---|---|---:|---|---|---|---|
| DPE-001 | TUP | 2024-09-18 | delisting / suspension / bankruptcy-like outcome | NYSE / ICE press release: trading suspended immediately after Chapter 11 disclosures | T-60..T+60 | delisted/suspended history retrieval and survivorship handling |
| DPE-002 | MULN | 2023-12-21 | reverse split | Mullen Automotive / GlobeNewswire: 1-for-100 reverse split effective Dec 21, 2023 | T-60..T+60 | reverse split adjustment, identifier continuity and raw/adjusted OHLCV |
| DPE-003 | CNGL | 2024-06-27 | trading halt / additional information requested | Nasdaq / GlobeNewswire: halt at 16:45:36 ET for news dissemination; status changed to additional information requested Jun 28, 2024 | T-10..T+10 | halt/suspension visibility and non-tradability representation |
| DPE-004 | ABAT | 2024-12-26 | offering / dilution | American Battery Technology Company press release: $10M registered direct offering with common stock and warrants | T-10..T+10 | offering/dilution event metadata, price/volume gap reconciliation |
| DPE-005 | WEYS | 2024-11-05 | special dividend / corporate action | Weyco Group / GlobeNewswire: special one-time cash dividend of $2.00 per share | T-60..T+60 | dividend/corporate-action metadata and adjusted/raw series coherence |

These five cases are mandatory for every provider evaluation.

## Frozen expansion slots

The provider plan requires an adversarial panel with at least 10 cases across mandatory categories. The following slots are frozen now and must be filled before execution if the evaluation proceeds beyond the seed panel.

| Event ID | Required category | Minimum evidence source | Window | Capability tested | Fill status |
|---|---|---|---|---|---|
| DPE-006 | second delisting / suspension / bankruptcy-like outcome | exchange notice, court/issuer filing, or official delisting/suspension release | T-60..T+60 | delisted history retrieval beyond TUP | TBD / must be frozen before provider query |
| DPE-007 | second reverse split | issuer press release, SEC filing, exchange corporate action notice | T-60..T+60 | reverse split handling beyond MULN | TBD / must be frozen before provider query |
| DPE-008 | second trading halt / regulatory halt | Nasdaq Trader, NYSE notice, FINRA halt notice, or official exchange halt record | T-10..T+10 | halt visibility beyond CNGL | TBD / must be frozen before provider query |
| DPE-009 | second offering / dilution / ATM-like event | issuer press release, SEC filing, prospectus supplement, or exchange filing | T-10..T+10 | dilution metadata beyond ABAT | TBD / must be frozen before provider query |
| DPE-010 | ticker change / merger / name change / identifier continuity event | issuer release, exchange notice, SEC filing or corporate-action source | T-60..T+60 | symbol/identifier continuity across corporate action | TBD / must be frozen before provider query |

## Required fields for filled expansion slots

Each filled expansion slot must record:

| Field | Requirement |
|---|---|
| `event_id` | DPE-006..DPE-010 |
| `ticker` | historical ticker at event date |
| `event_date` | official event date |
| `category` | one frozen category from the expansion table |
| `independent_source` | source independent of provider being evaluated |
| `source_title` | title or short citation |
| `source_url_or_archive_ref` | URL, archive reference, SEC accession or exchange notice ID |
| `window` | T-10..T+10 or T-60..T+60 as predefined |
| `capability_tested` | provider capability under test |
| `freeze_timestamp` | date/time the event was frozen |
| `selected_before_provider_query` | must be `yes` |

## Provider evaluation rule

Every provider candidate must be evaluated on the same frozen panel.

Provider-specific exclusions are not allowed unless the exclusion itself becomes a failure or caveat.

```text
NO PROVIDER QUERY BEFORE PANEL FREEZE
NO REPLACING FAILING EVENTS AFTER PROVIDER QUERY
NO USING PROVIDER COVERAGE TO SELECT EVENTS
NO DROPPING DELISTED/HARD EVENTS FOR CONVENIENCE
```

## Evaluation fields per provider-event pair

When provider evaluation is executed, each provider-event pair must produce:

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

## Stop rules

Stop provider evaluation if any of the following occurs:

- the panel is not fully frozen before provider query;
- provider license forbids local research artifact retention;
- delisted/suspended symbols cannot be reconstructed and the failure is silent;
- corporate-action adjustment method cannot be audited;
- point-in-time universe support is absent and no compatible independent universe source exists;
- provider query results cannot be reproduced or snapshotted.

## Governance consequence

Current status remains:

```text
SMALL-CAP TRIALS: BLOCKED
YFINANCE DAILY ALONE: NOT USABLE AS PRIMARY EVIDENCE
PROVIDER EVALUATION: PANEL FROZEN / NOT EXECUTED
TRIAL-XMOM-001: NOT AUTHORIZED
```

A future provider evaluation may use this panel, but a provider pass remains necessary and not sufficient. A separate methodology gate is still required before any small-cap strategy trial.

## Update 2026-05-17 - Expansion slots filled

Expansion slots `DPE-006..DPE-010` are now filled in [[Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17]].

Final expansion set:

- `FSR`
- `PHUN`
- `GH`
- `ICU`
- `DWAC -> DJT`

The proposed `CCB` July 2024 offering was rejected during verification because retrieved public sources indicated a December 2024 offering, not July. `ICU` / SeaStar Medical was substituted with verified July 10, 2024 registered-direct-offering evidence.
