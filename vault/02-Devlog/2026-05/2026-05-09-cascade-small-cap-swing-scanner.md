---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-swing-scanner
tags: [devlog, small-cap, scanner, rule-based, tdd]
---

# 2026-05-09 - Small-Cap Swing Scanner

## Contesto

Dopo universe builder, data-quality report e market-regime guardrail, la milestone successiva era il primo scanner rule-based long-only per setup small/mid-cap. Lo scanner non usa ML e non modifica la pipeline large-cap congelata.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_swing_scanner.py`.
- Modulo `src/scanner/small_cap_swing_scanner.py`.
- Config `SmallCapSwingScannerConfig`.
- Funzione `add_small_cap_swing_scanner_columns`.
- Funzione `latest_small_cap_candidates`.

## Setup supportati

```text
panic_reversal
breakout_continuation
post_gap_drift
```

Output aggiunti:

```text
small_cap_setup
small_cap_scanner_score
small_cap_scanner_pass
small_cap_scanner_reason
small_cap_scanner_reject_reason
```

Per compatibilita' futura vengono valorizzate anche:

```text
scanner_score
scanner_pass
scanner_reason
```

## Guardrail scanner iniziali

Lo scanner fallisce chiuso su campi OHLCV/volume/ATR mancanti e rifiuta setup con:

```text
relative_volume_below_min
atr_pct_below_min
atr_pct_above_max
gap_above_max
```

Il gap massimo default e' 10%, coerente con la spec che richiede di evitare open gap troppo estremi nella prima versione.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_swing_scanner.py
6 passed
```

## Prossima mossa

La prossima milestone e' execution assumptions dedicate: no naive next-open, skip gap apertura estremo, spread/slippage conservativi e no fill se liquidita' insufficiente.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-market-regime-guardrail]], [[Roadmap-Master]].
