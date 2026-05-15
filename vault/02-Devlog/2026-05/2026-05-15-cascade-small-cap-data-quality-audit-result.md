---
tipo: devlog
data: 2026-05-15
agente: cascade
topic: small-cap-data-quality-audit-result
tags: [devlog, small-cap, data-quality, yfinance, audit-result]
---

# 2026-05-15 - Small-cap data quality audit result

## Scope

Executed the pre-registered data-quality audit only.

```text
No strategy backtest.
No validation.
No OOS.
No sweep.
No TRIAL-XMOM-001.
```

## Frozen event list

The event list was frozen before querying `yfinance`:

- `TUP` delisting/suspension;
- `MULN` reverse split;
- `CNGL` trading halt;
- `ABAT` registered direct offering;
- `WEYS` special cash dividend.

## Result

```text
FINAL VERDICT: NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE
```

Key failures:

- `TUP` not downloadable from `yfinance` for a known delisting/suspension event.
- `MULN` not downloadable from `yfinance` for a known reverse split event window.
- `CNGL` downloadable but halt not explicitly encoded and zero-volume fraction is high.

## Governance consequence

```text
NO TRIAL-XMOM-001 WITH YFINANCE DAILY ALONE
NO NEW SMALL-CAP TRIAL USING CURRENT FREE-DATA PIPELINE AS PRIMARY EVIDENCE
```

Allowed next work:

- evaluate provider replacement / point-in-time data;
- consider negative-control methodology on a more reliable universe;
- Methodology Gate and Backtester Audit Plan remain useful but do not unlock small-cap yfinance trials.

Vedi [[Report-Small-Cap-Data-Quality-Audit-Result-2026-05-15]], [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]], [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
