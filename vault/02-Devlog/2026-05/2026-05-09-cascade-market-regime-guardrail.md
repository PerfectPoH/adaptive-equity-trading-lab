---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: market-regime-guardrail
tags: [devlog, small-cap, market-regime, risk, tdd]
---

# 2026-05-09 - Market-Regime No-Trade Guardrail

## Contesto

La spec small-cap richiede che il regime di mercato non sia solo osservato, ma diventi una regola operativa. In regime sfavorevole lo scanner puo' girare, ma i segnali/trade devono essere bloccati.

## Cosa e' stato aggiunto

- Test `tests/test_market_regime_guardrail.py`.
- Modulo `src/risk/market_regime_guardrail.py`.
- Config `MarketRegimeGuardrailConfig`.
- Funzione `add_market_regime_guardrail_columns`.

## Regole operative implementate

Default:

```text
IWM close deve essere >= IWM EMA 50
VIX close deve essere <= 35
dati regime mancanti => no-trade
```

Opzionali:

```text
require_iwm_above_ema_200
min_small_cap_breadth
```

Output aggiunti:

```text
market_regime_guardrail_config
market_regime_trade_allowed
market_regime_block_reason
signal_before_market_regime_guardrail
signal
```

Se la colonna `signal` esiste, il guardrail conserva il valore precedente in `signal_before_market_regime_guardrail` e forza `signal=False` quando il regime non permette trade.

## Verification

Test mirato:

```text
python -m pytest tests/test_market_regime_guardrail.py
5 passed
```

## Prossima mossa

Integrare il guardrail nel futuro scanner/backtest small-cap dedicato e definire come costruire le colonne regime da IWM, VIX e breadth. La pipeline large-cap congelata non e' stata modificata.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-data-quality]], [[Roadmap-Master]].
