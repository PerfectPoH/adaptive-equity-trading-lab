---
tipo: devlog
data: 2026-05-15
agente: cascade
topic: nctrl-scaffolding-check
tags: [devlog, negative-control, scaffolding, large-cap, governance]
---

# 2026-05-15 - NCTRL scaffolding check

## Scope

Executed `RESEARCH-046` as a technical scaffolding check only.

```text
No trial accounting.
No strategy validation.
No edge interpretation.
TRIAL-NCTRL-001 not opened.
```

## Config source

```text
experiments/configs/nctrl_scaffolding.py
```

The module freezes the baseline universe, universe-scope config changes, output path and manifest extras.

## Command

```powershell
.\.venv-lab\Scripts\python.exe -m experiments.configs.nctrl_scaffolding
```

## Result

```text
TECHNICAL_PASS
```

Summary:

```text
output_dir: experiments/runs/nctrl_scaffolding_2024_20260515
run_id: run_nctrl_scaffolding_20260515
config_hash: 732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab
manifest_purpose: nctrl_scaffolding_check
trial_accounting_present: false
all_required_artifacts_present: true
candidate_rows: 2500
candidate_days: 250
operational_candidates_total: 32
avg_operational_candidates_per_day: 0.128
days_with_operational_candidate: 27
pct_days_with_operational_candidate: 10.8%
portfolio_total_trades: 32
```

## Interpretation

The legacy small-cap pipeline can run end-to-end on the fixed large-cap/ETF control universe when only universe-scope config is adapted.

The portfolio result is not interpreted as strategy evidence.

## Next allowed step

Write the single-document `TRIAL-NCTRL-001` preregistration as a property-based negative control.

Vedi [[Report-Negative-Control-Scaffolding-Check-2026-05-15]], [[Report-Small-Cap-Lessons-Learned-Data-Quality-2026-05-15]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
