---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-data-quality-audit-spec
tags: [devlog, small-cap, data-quality, yfinance, audit-spec]
---

# 2026-05-14 - Small-cap data quality audit spec

## Obiettivo

Formalizzare il primo sotto-gate del Data Quality + Methodology Gate prima di qualunque nuovo trial small-cap.

## Decisione

Creata la spec:

```text
Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14
```

Stato:

```text
SPEC PRE-REGISTERED / NOT EXECUTED / NO TRIAL UNLOCKED
```

## Contenuto

La spec definisce:

- criteri di selezione eventi indipendenti da `yfinance`;
- categorie obbligatorie: delisting/suspension, reverse split, halt, corporate action, offering/dilution;
- proprieta' da verificare su OHLCV, adjusted data, halt awareness, survivorship e pipeline compatibility;
- soglie pre-registrate per `usable`, `usable_with_caveats`, `not_usable`;
- output atteso per un futuro audit result.

## Stato operativo

```text
No ticker list compiled.
No yfinance download.
No backtest.
No validation.
No OOS.
No TRIAL-XMOM-001.
```

Vedi [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]], [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
