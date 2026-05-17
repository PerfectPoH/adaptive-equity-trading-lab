---
tipo: event-panel-expansion
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: EXPANSION_SLOTS_FILLED_PROVIDER_QUERY_NOT_EXECUTED
scope: data_provider_methodology_gate
---

# Report Small-Cap Data Provider Event Panel Expansion - 2026-05-17

## Status

```text
EXPANSION SLOTS FILLED
PROVIDER QUERY NOT EXECUTED
NO PROVIDER SELECTED
NO PRICING DECISION
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document fills expansion slots `DPE-006` through `DPE-010` from [[Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17]].

The events were selected and checked against public issuer, exchange or official-source documents before any data-provider query.

## Verification note

The proposed `CCB` July 2024 offering event was not accepted as written. Public search results found Coastal Financial (`CCB`) offering references around December 2024, not July 2024. To avoid freezing an incorrect event, `DPE-009` is filled with `ICU` / SeaStar Medical, whose July 10, 2024 registered direct offering is supported by issuer/GlobeNewswire text.

## Expanded adversarial event panel

| Event ID | Ticker | Event date | Category | Independent source | Window | Capability tested |
|---|---|---:|---|---|---|---|
| DPE-006 | FSR | 2024-03-25 | second delisting / suspension / bankruptcy-like outcome | ICE / NYSE press release, "NYSE to Commence Delisting Proceedings Against Fisker Inc. (FSR)" | T-60..T+60 | delisting-proceeding and immediate-suspension handling; historical retrieval after exchange removal |
| DPE-007 | PHUN | 2024-02-27 | second reverse split | Phunware / GlobeNewswire, "Phunware Announces Reverse Stock Split" | T-60..T+60 | 1-for-50 reverse split adjustment, raw/adjusted continuity, volume adjustment sanity |
| DPE-008 | GH | 2024-05-23 | second trading halt / regulatory-news halt | Guardant Health investor relations / BusinessWire, "Guardant Health Stock Trading Temporarily Halted..." | T-10..T+10 | halt visibility and daily/intraday non-tradability representation |
| DPE-009 | ICU | 2024-07-10 | second offering / dilution / registered direct offering | SeaStar Medical / GlobeNewswire, "$10 Million Registered Direct Offering Priced At-the-Market Under Nasdaq Rules" | T-10..T+10 | offering/dilution metadata, price/volume discontinuity without split-like adjustment |
| DPE-010 | DWAC -> DJT | 2024-03-26 | ticker change / SPAC merger / business combination | Trump Media & Technology Group / GlobeNewswire, "Stock to Begin Trading Under Ticker Symbol DJT" | T-60..T+60 | ticker/identifier continuity across business combination |

## Source details

### DPE-006 - FSR delisting/suspension

- **Ticker:** `FSR`
- **Company:** Fisker Inc.
- **Event date:** 2024-03-25
- **Event type:** NYSE delisting proceedings and immediate trading suspension.
- **Source URL:** https://ir.theice.com/press/news-details/2024/NYSE-to-Commence-Delisting-Proceedings-Against-Fisker-Inc.-FSR/default.aspx
- **Verified text:** NYSE announced that NYSE Regulation determined to commence proceedings to delist Fisker Class A common stock and that trading would be suspended immediately.
- **Provider capability tested:** a provider must retain historical OHLCV and identifier history for a symbol that was suspended and later removed from exchange trading.

### DPE-007 - PHUN reverse split

- **Ticker:** `PHUN`
- **Company:** Phunware, Inc.
- **Event date:** 2024-02-27 post-split trading; effective 2024-02-26 after 5 PM ET.
- **Event type:** 1-for-50 reverse stock split.
- **Source URL:** https://www.globenewswire.com/news-release/2024/02/23/2834448/0/en/Phunware-Announces-Reverse-Stock-Split.html
- **Verified text:** Phunware announced a 1-for-50 reverse stock split effective as of 5 PM ET on February 26, 2024, with common stock trading post-split adjusted at market open on February 27, 2024.
- **Provider capability tested:** a provider must handle price and volume adjustment consistently and preserve raw/adjusted distinction.

### DPE-008 - GH trading halt

- **Ticker:** `GH`
- **Company:** Guardant Health, Inc.
- **Event date:** 2024-05-23
- **Event type:** Nasdaq temporary trading halt pending FDA advisory committee panel.
- **Source URL:** https://investors.guardanthealth.com/press-releases/press-releases/2024/Guardant-Health-Stock-Trading-Temporarily-Halted-FDA-Panel-to-Assess-Premarket-Approval-Application-for-Shield-Blood-Test-for-Colorectal-Cancer-Screening/default.aspx
- **Verified text:** Guardant Health announced that Nasdaq had temporarily halted trading of the company's stock while an FDA advisory committee panel reviewed the Shield blood test PMA application.
- **Provider capability tested:** daily data must not silently imply normal continuous trading, and intraday data must not fabricate bars during halt periods.

### DPE-009 - ICU registered direct offering

- **Ticker:** `ICU`
- **Company:** SeaStar Medical Holding Corporation
- **Event date:** 2024-07-10 announcement; expected closing around 2024-07-11.
- **Event type:** $10 million registered direct offering plus concurrent private placement warrants.
- **Source URL:** https://www.globenewswire.com/news-release/2024/07/10/2911162/0/en/SeaStar-Medical-Announces-10-Million-Registered-Direct-Offering-Priced-At-the-Market-Under-Nasdaq-Rules.html
- **Verified text:** SeaStar Medical announced an aggregate issuance and sale of 947,868 shares or equivalents at $10.55 per share/equivalent in a registered direct offering, plus concurrent warrants.
- **Provider capability tested:** provider must represent offering-driven price and volume changes as raw market events, not as split/dividend-style adjusted discontinuities.

### DPE-010 - DWAC to DJT ticker change / business combination

- **Tickers:** `DWAC` -> `DJT`
- **Company:** Digital World Acquisition Corp. / Trump Media & Technology Group
- **Event date:** 2024-03-26
- **Event type:** business combination with ticker switch.
- **Source URL:** https://www.globenewswire.com/news-release/2024/03/26/2852439/0/en/Trump-Media-Technology-Group-Stock-to-Begin-Trading-Under-Ticker-Symbol-DJT.html
- **Verified text:** Trump Media & Technology Group announced trading would begin on Nasdaq on March 26, 2024 and that at market open the ticker would switch from `DWAC` to `DJT`.
- **Provider capability tested:** provider must preserve identifier continuity across pre- and post-combination symbols and avoid empty historical arrays for pre-change windows.

## Filled slot status

```text
DPE-006: FILLED
DPE-007: FILLED
DPE-008: FILLED
DPE-009: FILLED_WITH_CORRECTION_CCB_REJECTED_ICU_ACCEPTED
DPE-010: FILLED
```

## Final panel after expansion

The full frozen provider evaluation panel is now:

| Event ID | Ticker / identifier | Category |
|---|---|---|
| DPE-001 | TUP | delisting / suspension / bankruptcy-like outcome |
| DPE-002 | MULN | reverse split |
| DPE-003 | CNGL | trading halt / additional information requested |
| DPE-004 | ABAT | offering / dilution |
| DPE-005 | WEYS | special dividend / corporate action |
| DPE-006 | FSR | second delisting / suspension / bankruptcy-like outcome |
| DPE-007 | PHUN | second reverse split |
| DPE-008 | GH | second trading halt / regulatory-news halt |
| DPE-009 | ICU | second offering / dilution / registered direct offering |
| DPE-010 | DWAC -> DJT | ticker change / SPAC merger / business combination |

## Execution rule

This expanded panel is frozen before provider evaluation.

```text
NO PROVIDER QUERY BEFORE PANEL FREEZE
NO REPLACING FAILING EVENTS AFTER PROVIDER QUERY
NO USING PROVIDER COVERAGE TO SELECT EVENTS
NO DROPPING DELISTED/HARD EVENTS FOR CONVENIENCE
```

## Governance consequence

Provider evaluation may now proceed against a complete 10-event adversarial panel, but no provider has been queried or selected.

A provider pass remains necessary but not sufficient. A separate methodology gate remains required before any small-cap strategy trial.
