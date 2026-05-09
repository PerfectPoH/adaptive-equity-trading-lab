---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-data-quality
tags: [devlog, small-cap, data-quality, tdd]
---

# 2026-05-09 - Small-Cap Data Quality Report

## Contesto

Dopo universe builder, la milestone successiva era un report di qualita' dati per candidati small/mid-cap. Questo serve prima di scanner, label e backtest per evitare conclusioni su dati sporchi.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_data_quality.py`.
- Modulo `src/data/small_cap_data_quality.py`.
- Config `SmallCapDataQualityConfig`.
- Funzione `build_small_cap_data_quality_report`.

## Controlli iniziali

Il report produce una riga per simbolo con:

```text
symbol
status
bars
start
end
zero_volume_fraction
max_abs_daily_return
warnings
errors
```

Stati:

```text
pass: nessun warning/error
warn: warning senza errori
fail: errori bloccanti o dati mancanti
```

Controlli:

- riuso di `validate_ohlcv`;
- dati mancanti;
- barre insufficienti;
- colonne OHLCV mancanti;
- gap calendario anomali;
- zero-volume fraction;
- extreme price jump proxy per split/reverse split/dati sporchi.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_data_quality.py
4 passed
```

## Prossima mossa

Aggiungere market-regime guardrail operativo o costruire il primo scanner rule-based long-only solo dopo aver definito come generare candidati e report data-quality da provider reali.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-universe-builder]], [[Roadmap-Master]].
