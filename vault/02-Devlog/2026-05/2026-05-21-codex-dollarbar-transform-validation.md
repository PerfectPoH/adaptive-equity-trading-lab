# Report DollarBar Transform Validation - 2026-05-21

Decision: `DOLLARBAR_TRANSFORM_REJECTED_FOR_DATA_LAYER`

## Scope

Distribution-only validation of static average-dollar bars versus rolling EMA dollar bars. No PnL, win rate, signal return, strategy return, provider query, backtest, paper/live trading or promotion was used.

## Result

- Evaluated files: 12
- EMA span: 20
- Coverage rate: 0.083333
- Median stability score delta: -3.556627

## Panel

- DBAR-001 AEHR delta=-6.220907 sample_ratio=0.494008 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-002 AEHR delta=-3.772909 sample_ratio=0.458689 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-003 ARRY delta=-28.912027 sample_ratio=0.467655 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-004 CABA delta=-0.192395 sample_ratio=0.266129 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-005 CABA delta=-0.623706 sample_ratio=0.430435 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-006 CABA delta=-1.367446 sample_ratio=0.351145 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-007 CABA delta=1.375045 sample_ratio=0.405405 verdict=PASS_DISTRIBUTION_STABILITY_GATE
- DBAR-008 CABA delta=-10.561056 sample_ratio=0.384025 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-009 CABA delta=-3.340346 sample_ratio=0.337104 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-010 CRMD delta=-14.870338 sample_ratio=0.382688 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-011 IOVA delta=-18.878711 sample_ratio=0.529172 verdict=FAIL_DISTRIBUTION_STABILITY_GATE
- DBAR-012 IOVA delta=-0.814129 sample_ratio=0.47018 verdict=FAIL_DISTRIBUTION_STABILITY_GATE


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
