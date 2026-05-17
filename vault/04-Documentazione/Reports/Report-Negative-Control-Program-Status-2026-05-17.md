---
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: NCTRL_PROGRAM_CLOSED
scope: methodology_negative_control
---

# Report Negative Control Program Status - 2026-05-17

## Executive decision

```text
NCTRL PROGRAM STATUS: CLOSED / TECHNICAL PASS
STRATEGY STATUS: NO PROMOTION
SMALL-CAP STATUS: STILL BLOCKED BY DATA QUALITY
NEXT WORK: DATA/INFRASTRUCTURE, NOT ALPHA SWEEP
```

The negative-control program has completed its intended purpose: verify that the research machinery can run a pre-registered property-check trial on a more reliable fixed large-cap/ETF universe.

This does not validate an investible edge.

## Program components

| Item | Status | Evidence | Decision |
|---|---|---|---|
| RESEARCH-046 | `TECHNICAL_PASS` | `run_nctrl_scaffolding_20260515`; config hash `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`; 32 portfolio trades | Scaffolding can generate end-to-end artifacts |
| TRIAL-NCTRL-001 preregistration | `PRE-REGISTERED` | [[Report-Negative-Control-Trial-001-Preregistration-2026-05-15]] | Trial scope frozen as property check, not strategy test |
| RESEARCH-047 | `COMPLETE` | Commit `bc18ec2`; P4/P5/P6/P7/P8 infrastructure and accounting wiring | Trial infrastructure complete |
| RESEARCH-048 / TRIAL-NCTRL-001 | `PROPERTY_CHECK_PASS` | Commit `3a05a3c`; `run_nctrl_trial_001_20260517`; P1-P8 pass | Machine property check passed |

## Final NCTRL result

`TRIAL-NCTRL-001` produced `PROPERTY_CHECK_PASS`.

Key run identity:

- Output directory: `experiments/runs/nctrl_trial_001_2024_20260517`
- Run ID: `run_nctrl_trial_001_20260517`
- Config source: `experiments/configs/nctrl_trial_001.py`
- Config hash: `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`
- Manifest period representation: `2024-01-02..2024-12-27`
- Frozen universe: AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ
- Property report: P1-P8 pass

The period end is accepted as the actual last candidate/trading-day representation for the requested `2024-01-02..2024-12-31` window.

## What this validates

The program validates the following engineering and methodology machinery:

- deterministic run manifests and trial accounting;
- end-to-end artifact generation;
- risk-fraction sizing regression coverage;
- cash-ledger timing fixture coverage;
- distribution-aware bootstrap random baseline with `N=1000`;
- random-entry sign-flip frequency reporting;
- ex-topN arithmetic checks;
- benchmark numerical sanity checks;
- property-check markdown/json reporting.

## What this does not validate

This program does not validate:

- an investible small-cap edge;
- the archived breakout/open-to-close strategy;
- production ranking;
- paper trading;
- live execution readiness;
- `yfinance` daily data as sufficient for distressed/small-cap trials;
- any new small-cap universe or momentum strategy.

## Standing governance

The following constraints remain active:

```text
NO PAPER TRADING
NO PRODUCTION RANKING
NO DISCRETIONARY PARAMETER SWEEP
NO TRIAL-RANKEX-002
NO TRIAL-XMOM-001 UNTIL DATA/METHODOLOGY GATE IS SATISFIED
NO SMALL-CAP TRIALS USING YFINANCE DAILY ALONE AS PRIMARY EVIDENCE
```

## Recommended next work

The next valid work is infrastructure/data work, not alpha optimization.

Allowed next tracks:

1. **Provider/data evaluation**
   - point-in-time universe support;
   - delisted symbols;
   - corporate actions and reverse-split handling;
   - halt/suspension representation;
   - dividend and split adjustment audit.

2. **Research machinery hardening**
   - formal property-check CLI;
   - run artifact manifest validation command;
   - reproducibility checks for ignored run artifacts;
   - report rebuild tooling.

3. **Non-small-cap methodology exploration**
   - only if separately pre-registered;
   - must define universe, data reliability, benchmarks, and stop rules before any run.

## Final decision

The NCTRL program is closed as a technical/methodology pass.

The project should not treat this as strategy progress. It is a gate proving that the machine can evaluate pre-registered properties on a reliable control universe. The next bottleneck remains data quality and point-in-time methodology for any future market-edge trial.
