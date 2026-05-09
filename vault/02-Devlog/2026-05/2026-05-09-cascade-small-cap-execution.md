---
tipo: devlog
data: 2026-05-09
agente: cascade
topic: small-cap-execution
tags: [devlog, small-cap, execution, backtest, tdd]
---

# 2026-05-09 - Conservative Small-Cap Execution Model

## Contesto

La spec small-cap richiede execution assumptions diverse dalla baseline large-cap. Il vecchio next-open non basta: servono gap guardrail, spread/slippage conservativi e limiti di liquidita'.

## Cosa e' stato aggiunto

- Test `tests/test_small_cap_execution.py`.
- Modulo `src/backtest/small_cap_execution.py`.
- Config `SmallCapExecutionConfig`.
- Funzione `add_small_cap_execution_columns`.

## Regole implementate

Default:

```text
max_next_open_gap: 10%
spread_bps: 50
slippage_bps: 50
risk_fraction: 1%
stop_atr_multiple: 1.5
take_profit_atr_multiple: 3.0
max_position_dollar_volume_fraction: 1%
min_trade_notional: 1000 USD
```

Output principali:

```text
small_cap_entry_reference_price
small_cap_next_open_gap_pct
small_cap_estimated_cost_pct
small_cap_entry_price
small_cap_stop_loss
small_cap_take_profit
small_cap_execution_valid
small_cap_execution_skip_reason
small_cap_position_size
small_cap_position_notional
small_cap_max_liquidity_notional
```

Skip reasons iniziali:

```text
no_next_open
missing_<field>
missing_next_open_gap
gap_above_max
missing_entry_price
missing_exit_levels
invalid_risk_reward
missing_avg_dollar_volume_20d
liquidity_cap_below_min_trade_notional
position_below_min_trade_notional
```

Il modello non modifica la pipeline large-cap congelata e non pretende ancora di essere un backtest small-cap completo: produce piani di esecuzione conservativi da usare nella prossima pipeline dedicata.

## Verification

Test mirato:

```text
python -m pytest tests/test_small_cap_execution.py
6 passed
```

## Prossima mossa

La prossima milestone e' rendere esplicito il capacity constraint/reporting oppure costruire un primo candidate-export giornaliero che unisce universe builder, data-quality, scanner, regime guardrail ed execution planner.

Vedi [[small-cap-swing-research-spec]], [[2026-05-09-cascade-small-cap-swing-scanner]], [[Roadmap-Master]].
