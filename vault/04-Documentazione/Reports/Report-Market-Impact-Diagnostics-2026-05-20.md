---
tipo: market-impact-diagnostics
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
run_id: run_f7f0a81b1142
artifact_dir: experiments/runs/provider_aware_oos_replay_bounded_20260520
---

# Report Market Impact Diagnostics - 2026-05-20

## Scope

Diagnostic review requested on the bounded replay to validate:

1. real participation rate (`position_notional / adv_notional`);
2. unit/scale sanity for the square-root impact formula.

Model under test:

```text
impact_bps = coefficient_bps * volatility * sqrt(order_notional / adv_notional)
impact_cost_pct = impact_bps / 10_000
```

Config from `run_manifest.json`:

- `impact_coefficient_bps = 50.0`
- `max_position_dollar_volume_fraction = 0.01`
- `impact_participation_cap = 0.20`

## Summary Statistics (27 trades)

- `impact_cost_pct`: min `2.63e-06`, median `5.52e-06`, max `2.11e-05`
- `impact_bps`: min `0.0263`, median `0.0552`, max `0.2111`
- `participation_rate`: min `0.000082`, median `0.000808`, max `0.009370`
- `volatility used`: min `0.0258`, median `0.0472`, max `0.0822`

Interpretation:

- impacts are tiny because participation is tiny (most orders are below `0.1%` ADV; worst case below `1%` ADV);
- no evidence of participation-cap saturation in this run (`max 0.94%` vs cap `20%`).

## Hypothesis 1 - Participation Rate Reality Check

`adv_notional` reconstructed as:

```text
adv_notional = max_liquidity_notional / max_position_dollar_volume_fraction
```

with `max_position_dollar_volume_fraction = 0.01`.

Findings:

- median participation `0.0808%` ADV;
- max participation `0.9370%` ADV;
- this is consistent with a conservative risk/liquidity sizing regime, so sub-1 bps impact is mathematically expected.

## Hypothesis 2 - Unit / Scale Sanity Check

Recomputed `impact_bps` from logged trade values:

```text
impact_bps_recomputed = 50.0 * volatility * sqrt(participation_rate)
```

Validation result:

- max absolute difference between observed and recomputed impact = `2.21e-06 bps` (numerical rounding only).

Conclusion:

- no unit mismatch detected in runtime wiring;
- volatility is being consumed as decimal (`0.04 = 4%`), consistently with formula intent;
- conversion from bps to pct (`/10_000`) is correct.

## Top 5 Impact-Penalized Trades

1. `CRMD` 2024-08-27: participation `0.2638%`, vol `0.0822`, impact `0.2111 bps`
2. `CRMD` 2024-04-08: participation `0.6943%`, vol `0.0487`, impact `0.2029 bps`
3. `CRMD` 2024-03-14: participation `0.9370%`, vol `0.0394`, impact `0.1909 bps`
4. `AEHR` 2025-05-28: participation `0.3080%`, vol `0.0415`, impact `0.1152 bps`
5. `AEHR` 2025-06-05: participation `0.2212%`, vol `0.0489`, impact `0.1149 bps`

## Diagnostic Verdict

```text
NO MATHEMATICAL BUG CONFIRMED
LOW IMPACT LEVELS EXPLAINED BY LOW PARTICIPATION
MODEL IS WORKING AS IMPLEMENTED
```

## Practical Next Calibration Step

If target realism requires larger small-cap friction, calibration is needed (not a bug fix):

- increase `impact_coefficient_bps` (e.g. stress test `150`, `300`, `500`);
- lower liquidity capacity (`max_position_dollar_volume_fraction`) to force stricter sizing, or test with larger order sizing for stress scenarios;
- compare equity/path sensitivity across these calibrated regimes before changing defaults.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
