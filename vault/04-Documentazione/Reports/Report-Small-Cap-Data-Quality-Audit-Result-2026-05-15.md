---
tipo: audit-result
progetto: adaptive-equity-trading-lab
data: 2026-05-15
tags: [audit, small-cap, data-quality, yfinance, survivorship, governance]
---

# Report Small-Cap Data Quality Audit Result - 2026-05-15

## Stato

```text
EVENT LIST FROZEN BEFORE YFINANCE QUERY
YFINANCE AUDIT EXECUTED FOR DATA-QUALITY ONLY
NO STRATEGY BACKTEST / NO VALIDATION / NO OOS / NO SWEEP
TRIAL-XMOM-001 NOT AUTHORIZED
FINAL VERDICT: NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE
```

Questo report esegue il primo sotto-gate definito in [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]].

## Event list frozen

La lista seguente e' stata selezionata da fonti indipendenti da `yfinance` prima di interrogare `yfinance`.

| Event ID | Ticker | Event date | Category | Independent source | Window | Key check |
|---|---|---:|---|---|---|---|
| DQ-001 | TUP | 2024-09-18 | delisting/suspension | NYSE / ICE press release: trading suspended immediately after Chapter 11 disclosures | T-60..T+60 | availability and delisting/suspension representation |
| DQ-002 | MULN | 2023-12-21 | reverse split | Mullen Automotive / GlobeNewswire: 1-for-100 reverse split effective Dec 21, 2023 | T-60..T+60 | split adjustment integrity |
| DQ-003 | CNGL | 2024-06-27 | trading halt | Nasdaq / GlobeNewswire: halt at 16:45:36 ET for news dissemination; status changed to additional information requested Jun 28, 2024 | T-10..T+10 | halt visibility and tradability representation |
| DQ-004 | ABAT | 2024-12-26 | offering/dilution | American Battery Technology Company press release: $10M registered direct offering with common stock and warrants | T-10..T+10 | offering gap and OHLCV representation |
| DQ-005 | WEYS | 2024-11-05 | corporate action price-impacting | Weyco Group / GlobeNewswire: special one-time cash dividend of $2.00 per share | T-60..T+60 | dividend/corporate-action representation |

## Fonte snippets

- DQ-001: NYSE announced delisting proceedings for TUP and immediate trading suspension after Chapter 11 disclosures.
- DQ-002: Mullen announced a 1-for-100 reverse stock split effective Dec 21, 2023, trading split-adjusted from market open.
- DQ-003: Nasdaq announced CNGL halt changed to additional information requested; trading had been halted Jun 27, 2024 at 16:45:36 ET.
- DQ-004: ABAT announced purchase agreements for 3,773,586 shares and warrants, gross proceeds approximately $10M, expected closing Dec 27, 2024.
- DQ-005: WEYS announced a special one-time cash dividend of $2.00 per share, payable Jan 2, 2025 to holders of record Nov 18, 2024.

## Audit execution

```text
EXECUTED
```

Command scope:

```text
download frozen tickers only
no metadata screening
no strategy signal
no benchmark
no portfolio simulation
no OOS
```

## Yfinance diagnostic output

| Event ID | Ticker | Downloadable | Bars | Window complete | First bar | Last bar | Zero-volume fraction | Max abs daily return | Actions detected | Raw issue |
|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| DQ-001 | TUP | no | 0 | no | n/a | n/a | n/a | n/a | none | `possibly delisted; no timezone found` |
| DQ-002 | MULN | no | 0 | no | n/a | n/a | n/a | n/a | none | `Quote not found` / `possibly delisted; no timezone found` |
| DQ-003 | CNGL | yes | 27 | partial | 2024-06-07 | 2024-07-17 | 40.74% | 5.47% | none | high zero-volume fraction; halt not explicitly encoded |
| DQ-004 | ABAT | yes | 26 | partial | 2024-12-06 | 2025-01-15 | 0.00% | 60.36% | none | offering visible only through price/volume path, not as event metadata |
| DQ-005 | WEYS | yes | 96 | yes | 2024-08-27 | 2025-01-14 | 0.00% | 18.96% | dividend 2024-11-18: 2.26 | corporate action detectable; amount includes regular plus special dividend |

## Per-event assessment

| Event ID | source_independent | yfinance_downloadable | event_window_complete | corporate_action_adjustment_ok | halt_or_suspension_visible | tradability_representation_ok | pipeline_warning_required | severity | verdict |
|---|---|---|---|---|---|---|---|---|---|
| DQ-001 | yes | no | no | not_applicable | no | no | yes | critical | fail |
| DQ-002 | yes | no | no | unclear | not_applicable | unclear | yes | high | fail |
| DQ-003 | yes | yes | partial | not_applicable | unclear | unclear | yes | high | caveat |
| DQ-004 | yes | yes | partial | not_applicable | not_applicable | unclear | yes | medium | caveat |
| DQ-005 | yes | yes | yes | yes | not_applicable | yes | yes | low | pass |

## Interpretation

The audit catches the core failure mode the gate was designed to test.

Two independently selected critical small-cap event cases are not recoverable from `yfinance` under their historical tickers:

- `TUP`: a known NYSE delisting/suspension event is not downloadable.
- `MULN`: a known reverse-split event window is not downloadable under the historical ticker.

This means an event-selected small-cap sample cannot be reconstructed reliably from `yfinance` daily data alone. The problem is not merely missing bars. It is survivorship/provider availability: the dataset can silently remove exactly the kind of distressed, delisted, renamed or corporate-action-heavy symbols that dominate small-cap tail risk.

The three downloadable cases do not rescue the dataset:

- `CNGL` downloads, but the halt is not explicitly represented as an event and the window has a high zero-volume fraction.
- `ABAT` downloads, but the registered direct offering is only visible indirectly through the price path.
- `WEYS` is the cleanest case; the dividend action is detectable, but this is also the least adversarial event in the sample.

## Pre-registered threshold evaluation

From [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]]:

```text
not_usable if critical failures >= 1
not_usable if high severity failures >= 3
not_usable if halt/suspension or delisting represented as normal trading in a non-detectable way
```

Observed:

```text
critical failures = 1
high severity failures = 2
pass_or_caveat = 3 / 5 = 60%
mandatory categories covered = yes
delisting/suspension category = not downloadable
```

The first `not_usable` condition is triggered.

## Final verdict

```text
NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE
```

This does not mean every `yfinance` daily bar is wrong. It means `yfinance` alone is not a reliable primary dataset for new small-cap strategy trials where delisting, split, halt, dilution and survivorship behavior are part of the risk surface.

## Governance consequence

```text
NO TRIAL-XMOM-001 WITH YFINANCE DAILY ALONE
NO NEW SMALL-CAP TRIAL USING CURRENT FREE-DATA PIPELINE AS PRIMARY EVIDENCE
NO PAPER TRADING
NO OOS
NO SWEEP
```

Allowed next work:

```text
1. provider replacement / point-in-time dataset evaluation
2. negative-control methodology on more reliable large-cap universe
3. Methodology Gate document can still be written, but it does not unlock small-cap trials without better data
4. Backtester Audit Plan remains useful infrastructure work
```

## Recommendation

Do not proceed to `TRIAL-XMOM-001` on the current `yfinance` small-cap data foundation.

The honest next decision is to either:

1. evaluate a better data provider with delisted symbols and corporate actions; or
2. move the next methodological validation to a more reliable universe where data availability is not the dominant failure mode.

Vedi [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]], [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
