---
tipo: devlog
data: 2026-05-10
agente: cascade
topic: small-cap-data-preparer
tags: [devlog, small-cap, data, features, runner, tdd]
---

# 2026-05-10 - Small-Cap Data Preparer

## Contesto

Dopo il runner storico small-cap, serviva uno strato testabile che trasformasse dati OHLCV gia' scaricati e metadata statici in input compatibili con candidate export, benchmark e report.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_data_preparer.py`.
- Modulo `src/data/small_cap_data_preparer.py`.
- Dataclass `SmallCapPreparedData`.
- Funzione `prepare_small_cap_historical_data`.

## Input

```text
raw_frames: dict[symbol, OHLCV]
iwm_frame: OHLCV IWM proxy
static_metadata: symbol, market_cap, is_etf
vix_frame opzionale
```

## Output

```text
SmallCapPreparedData(
  candidate_metadata,
  frames,
  iwm_frame,
  diagnostics,
)
```

## Colonne prodotte

Per ogni frame simbolo vengono aggiunte le feature richieste da scanner, regime guardrail ed execution planner:

```text
atr
atr_pct
relative_volume_20d
distance_from_20d_high
rolling_volatility_20d
avg_volume_20d
avg_dollar_volume_20d
iwm_close
iwm_ema_50
iwm_ema_200
vix_close
```

## Metadata candidate

Il preparer costruisce:

```text
symbol
market_cap
price
avg_volume_20d
avg_dollar_volume_20d
is_etf
```

Queste colonne alimentano direttamente `build_small_cap_universe` e `run_small_cap_historical_report`.

## Diagnostica

Il risultato include:

```text
missing_frame_symbols
empty_frame_symbols
raw_symbols_without_metadata
```

## Nota metodologica

Questo modulo non scarica ancora dati da provider esterni. E' lo strato deterministico tra raw OHLCV e runner storico. Il download reale puo' essere aggiunto sopra, mantenendo questo livello testabile e riproducibile.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_data_preparer.py
3 passed
```

## Prossima mossa

Aggiungere un orchestratore/CLI che scarichi ticker small-cap, IWM e VIX, costruisca metadata statici e chiami `prepare_small_cap_historical_data` + `run_small_cap_historical_report`.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-historical-runner]], [[Roadmap-Master]].
