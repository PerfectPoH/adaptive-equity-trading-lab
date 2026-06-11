# Report GAPREV End-To-End Controlled Run - 2026-05-21

Status: TECHNICAL_CONTROLLED_RUN_COMPLETE__NO_PROMOTION

## Eight-Point Chain
- 1_provider_selection_gate: PROVIDER_SELECTED_FOR_SINGLE_CONTROLLED_PROBE
- 2_single_provider_probe_approval: APPROVED_SINGLE_PROVIDER_PROBE
- 3_intraday_data_ingestion_gate: pass
- 4_parameter_freeze: PARAMETERS_FROZEN_FOR_SINGLE_CONTROLLED_PROBE
- 5_pre_run_gate: pass
- 6_single_controlled_backtest: pass
- 7_post_run_validation: pass
- 8_decision: NO_PROMOTION

## Probe
- Provider: Databento Historical
- Dataset/schema: XNAS.ITCH / ohlcv-1m
- Rows retained: 662
- Raw payload retained: false

## Controlled Backtest
- Execution status: pass
- Trade count: 0
- Gap return: 0.05094130675526043
- Relative opening volume: 5.654788694082445
- Gross return: None
- Net return after 500 bps round-trip cost: None

## Decision
No promotion. This was a single-symbol, single-event, known-forensic controlled probe. It validates wiring and data handling, not a deployable edge.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
