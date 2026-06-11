"""TRIAL-PCTRL-001 — Positive Control & DSR Power Curve.

Companion to ``nctrl_trial_001``. Where NCTRL verifies that the pipeline
rejects random entries, PCTRL verifies that the *gates* (DSR + N_eff)
accept a known synthetic edge and measures the minimum sample size
required for them to do so. Together they bound the gate's calibration
from both sides.

Run::

    python -m experiments.configs.pctrl_synthetic_edge_001
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.experiments.pctrl_synthetic_edge_simulator import (
    PowerCurveSpec,
    minimum_sample_size_for_power,
    run_power_curve,
)


RUN_ID = "run_pctrl_synthetic_edge_001_20260610"
TRIAL_ID = "TRIAL-PCTRL-001"
OUTPUT_DIR = Path("experiments/runs/pctrl_synthetic_edge_001_20260610")

# Coverage rationale:
# - sample_sizes span the empirical range of trade counts observed in the
#   archive (XMOM ~11–43, GapRev ~20–30) up to a "well-funded" trial.
# - effect_sizes are per-trade means with sigma=0.02 (~typical equity day
#   stdev). Effect 0.000 is the negative control — should yield ~5% pass rate
#   if the gate is calibrated; we expect lower because the gate is conservative.
# - trial_count_searched=30 reflects the program-level multiplicity (XMOM,
#   GapRev, candidates 004–018 etc. ≈ 30 attempts).
POWER_CURVE_SPEC = PowerCurveSpec(
    sample_sizes=(10, 20, 30, 50, 75, 100, 150, 200, 252, 400, 600),
    effect_sizes=(0.0, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.0075, 0.010),
    return_volatility=0.02,
    trial_count_searched=30,
    noise_trials_for_dispersion=30,
    bootstrap_iterations=300,
    confidence_threshold=0.95,
    base_seed=1701,
)


def run_pctrl_trial_001() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = run_power_curve(POWER_CURVE_SPEC)

    min_n_80 = minimum_sample_size_for_power(results, target_power=0.80)
    min_n_50 = minimum_sample_size_for_power(results, target_power=0.50)

    matrix_rows = [asdict(cell) for cell in results]
    payload: dict[str, Any] = {
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "spec": {
            "sample_sizes": list(POWER_CURVE_SPEC.sample_sizes),
            "effect_sizes": list(POWER_CURVE_SPEC.effect_sizes),
            "return_volatility": POWER_CURVE_SPEC.return_volatility,
            "trial_count_searched": POWER_CURVE_SPEC.trial_count_searched,
            "noise_trials_for_dispersion": POWER_CURVE_SPEC.noise_trials_for_dispersion,
            "bootstrap_iterations": POWER_CURVE_SPEC.bootstrap_iterations,
            "confidence_threshold": POWER_CURVE_SPEC.confidence_threshold,
            "base_seed": POWER_CURVE_SPEC.base_seed,
        },
        "results": matrix_rows,
        "minimum_sample_size_for_power_50": {f"{k:.4f}": v for k, v in min_n_50.items()},
        "minimum_sample_size_for_power_80": {f"{k:.4f}": v for k, v in min_n_80.items()},
    }

    (OUTPUT_DIR / "power_curve_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report_md = _format_markdown_report(payload, results, min_n_50, min_n_80)
    (OUTPUT_DIR / "power_curve_report.md").write_text(report_md, encoding="utf-8")

    matrix_csv = _format_matrix_csv(results)
    (OUTPUT_DIR / "power_curve_matrix.csv").write_text(matrix_csv, encoding="utf-8")
    return payload


def _format_matrix_csv(results: list) -> str:
    header = (
        "sample_size,effect_size_mean,return_volatility,annualized_edge_sharpe,"
        "trial_count_searched,bootstrap_iterations,pass_count,pass_rate,"
        "mean_observed_sharpe,mean_dsr,mean_benchmark_sharpe\n"
    )
    lines = [header]
    for cell in results:
        lines.append(
            ",".join(
                str(value)
                for value in (
                    cell.sample_size,
                    cell.effect_size_mean,
                    cell.return_volatility,
                    round(cell.annualized_edge_sharpe, 6),
                    cell.trial_count_searched,
                    cell.bootstrap_iterations,
                    cell.pass_count,
                    round(cell.pass_rate, 6),
                    round(cell.mean_observed_sharpe, 6),
                    round(cell.mean_dsr, 6),
                    round(cell.mean_benchmark_sharpe, 6),
                )
            )
            + "\n"
        )
    return "".join(lines)


def _format_markdown_report(
    payload: dict[str, Any],
    results: list,
    min_n_50: dict[float, int | None],
    min_n_80: dict[float, int | None],
) -> str:
    spec = payload["spec"]
    lines: list[str] = []
    lines.append(f"# {payload['trial_id']} - Positive Control & DSR Power Curve")
    lines.append("")
    lines.append(f"Run ID: `{payload['run_id']}`")
    lines.append(f"Generated: `{payload['generated_at_utc']}`")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- Per-trade return volatility (sigma): `{spec['return_volatility']}`")
    lines.append(f"- Trial count searched (program-level multiplicity): `{spec['trial_count_searched']}`")
    lines.append(f"- Noise trials used to estimate sharpe_std: `{spec['noise_trials_for_dispersion']}`")
    lines.append(f"- Bootstrap iterations per cell: `{spec['bootstrap_iterations']}`")
    lines.append(f"- DSR confidence threshold: `{spec['confidence_threshold']}`")
    lines.append("")
    lines.append("## Empirical pass rate (= power for effect>0, type-I for effect=0)")
    lines.append("")
    header_cells = ["N \\ mu"] + [f"{e:.4f}" for e in spec["effect_sizes"]]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("| " + " | ".join("---" for _ in header_cells) + " |")
    by_n: dict[int, dict[float, float]] = {}
    for cell in results:
        by_n.setdefault(cell.sample_size, {})[cell.effect_size_mean] = cell.pass_rate
    for n in spec["sample_sizes"]:
        row = [str(n)] + [f"{by_n[n][e]:.2f}" for e in spec["effect_sizes"]]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Minimum sample size for target power")
    lines.append("")
    lines.append("| effect_size_mean | annualized Sharpe (approx) | min N for 50% power | min N for 80% power |")
    lines.append("| --- | --- | --- | --- |")
    import math
    for effect in spec["effect_sizes"]:
        ann_sharpe = effect / spec["return_volatility"] * math.sqrt(252)
        n50 = min_n_50.get(effect)
        n80 = min_n_80.get(effect)
        lines.append(
            f"| {effect:.4f} | {ann_sharpe:.2f} | {n50 if n50 is not None else 'not reached'} | {n80 if n80 is not None else 'not reached'} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- The `effect_size_mean = 0` row is the negative-control replication: the")
    lines.append("  empirical pass rate should be at or below the nominal type-I rate (~5%).")
    lines.append("  Values below that show the gate is **conservative** at small N.")
    lines.append("- Effect sizes are per-trade means. With sigma=0.02, the annualized Sharpe")
    lines.append("  column lets you compare to public-domain figures.")
    lines.append("- The `min N for 80% power` column tells you how many trades a trial needs")
    lines.append("  before the DSR gate can detect a given true edge. Trials with fewer trades")
    lines.append("  than this threshold cannot pass the gate even if they hold a real edge,")
    lines.append("  and a passing result at lower N is dominated by luck.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = run_pctrl_trial_001()
    print(json.dumps({"trial_id": payload["trial_id"], "run_id": payload["run_id"], "output_dir": str(OUTPUT_DIR)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
