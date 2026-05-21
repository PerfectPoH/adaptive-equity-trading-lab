# XMOM Earnings Provider Selection Gate - 2026-05-21

Status:

```text
SPEC_ONLY_NOT_QUERIED
```

This gate defines the provider and data-source requirements that must be satisfied before implementing an earnings-event extractor for `TRIAL-XMOM-CATALYST-001`.

It does not authorize provider queries, network calls, market-data downloads, OOS execution, paper/live trading or strategy promotion.

## Required Provider Properties

- historical earnings-calendar coverage for US small caps;
- report-time flags equivalent to BMO, AMC, DMT or UNSPECIFIED;
- ability to estimate `UNSPECIFIED` rate before ingestion;
- point-in-time symbol universe plan or explicit survivorship-bias caveat;
- deterministic handling for delisted/acquired symbols;
- licensing and retention policy;
- rate-limit policy before any probe.

## Reaction-Session Contract

```text
BMO -> same_trading_session
AMC -> next_trading_session
DMT -> purge
UNSPECIFIED -> purge
```

## Decision

No extractor may be implemented until this provider gate is valid and a separate probe approval is created.
