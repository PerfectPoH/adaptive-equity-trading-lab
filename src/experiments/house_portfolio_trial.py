"""TRIAL-HOUSE-001: la ricetta congelata + la difesa validata, come oggetto unico.

"Portfolio della casa" = path dinamico per-regime (regola preregistrata,
vol-norm, TRIAL-STUDIO-OOS-005/006) x esposizione del regime classifier
(unico overlay difensivo sopravvissuto al duello), con costi di rebalancing
dichiarati.

Regole fissate prima di leggere i risultati:
  - exposure: HIGH_VOL -> 0.25, TREND_DOWN -> 0.50, altrimenti 1.0
  - costo: 10 bps per unita' di esposizione scambiata (|delta exposure|)
  - gates: H1 OOS positivo; H2 return/maxDD migliore del path non difeso;
    H3 DSR pass (trial_count=2, combo preregistrata);
    H4 coerenza su ENTRAMBI i cutoff (2025 e 2024).

Diagnostico su stream proxy vol-normalizzati: nessuna promozione.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.kronos_defense_trial import KronosDefenseConfig, classifier_exposure_series
from src.validation.deflated_sharpe import deflated_sharpe_ratio_from_returns


@dataclass(frozen=True)
class HouseConfig:
    cost_bps_per_turnover: float = 10.0
    dsr_trial_count: float = 2.0
    dsr_sharpe_std: float = 0.30  # ordine di grandezza della cross-section osservata
    dsr_confidence: float = 0.95


def _returns_from_curve(cumulative: pd.Series) -> pd.Series:
    return (1.0 + cumulative) / (1.0 + cumulative.shift(1).fillna(0.0)) - 1.0


def _metrics(returns: pd.Series) -> dict[str, float]:
    curve = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    total = float(curve.iloc[-1] - 1.0)
    max_dd = float(drawdown.min())
    return {
        "total_return": round(total, 6),
        "max_drawdown": round(max_dd, 6),
        "return_over_drawdown": round(total / abs(max_dd), 4) if max_dd < 0 else float("inf"),
    }


def run_house_portfolio_trial(
    oos_curves: pd.DataFrame,
    regime_history: pd.DataFrame,
    config: HouseConfig | None = None,
) -> dict[str, Any]:
    cfg = config or HouseConfig()
    periods = pd.DatetimeIndex(pd.to_datetime(oos_curves["period"], errors="coerce"))
    dynamic_returns = _returns_from_curve(pd.Series(oos_curves["dynamic"].to_numpy(), index=periods))
    static_returns = _returns_from_curve(pd.Series(oos_curves["static"].to_numpy(), index=periods))

    exposure = classifier_exposure_series(periods, regime_history, KronosDefenseConfig())
    turnover = exposure.diff().abs().fillna(0.0)
    cost = turnover * (cfg.cost_bps_per_turnover / 10_000.0)
    house_returns = dynamic_returns * exposure - cost

    house = _metrics(house_returns)
    undefended = _metrics(dynamic_returns)
    static = _metrics(static_returns)
    dsr = deflated_sharpe_ratio_from_returns(
        house_returns.fillna(0.0).to_numpy(),
        trial_count=cfg.dsr_trial_count,
        sharpe_std=cfg.dsr_sharpe_std,
        confidence_threshold=cfg.dsr_confidence,
    )
    gates = {
        "H1_oos_positive": house["total_return"] > 0,
        "H2_better_risk_adjusted_than_undefended": house["return_over_drawdown"] > undefended["return_over_drawdown"],
        "H3_dsr_pass": bool(dsr.passed),
    }
    return {
        "status": "HOUSE_PORTFOLIO_TRIAL_COMPLETE",
        "house": {**house, "mean_exposure": round(float(exposure.mean()), 4), "total_cost_paid": round(float(cost.sum()), 6)},
        "undefended_dynamic": undefended,
        "static": static,
        "statistical_gate": {
            "observed_sharpe_daily": round(dsr.observed_sharpe, 6),
            "dsr": round(dsr.dsr, 6),
            "dsr_passed": bool(dsr.passed),
            "trial_count": cfg.dsr_trial_count,
        },
        "gates": gates,
        "promotion_allowed": False,
        "provider_query_performed": False,
    }


def run_house_trial_on_runs(run_globs: list[str], regime_history_path: Path) -> dict[str, Any]:
    regime_history = pd.read_csv(regime_history_path)
    per_run: dict[str, dict[str, Any]] = {}
    for pattern in run_globs:
        candidates = sorted(Path("experiments/runs").glob(pattern))
        if not candidates:
            per_run[pattern] = {"status": "RUN_NOT_FOUND"}
            continue
        curves = pd.read_csv(candidates[-1] / "oos_curves.csv")
        per_run[pattern] = run_house_portfolio_trial(curves, regime_history)
    completed = [r for r in per_run.values() if r.get("status") == "HOUSE_PORTFOLIO_TRIAL_COMPLETE"]
    h4 = len(completed) >= 2 and all(all(r["gates"].values()) for r in completed)
    individual_pass = [all(r["gates"].values()) for r in completed]
    verdict = "HOUSE_PASS_ALL_GATES_BOTH_CUTOFFS" if h4 else (
        "HOUSE_PARTIAL_" + "_".join("PASS" if p else "FAIL" for p in individual_pass) if completed else "HOUSE_NO_RUNS"
    )
    return {
        "trial_id": "TRIAL-HOUSE-001",
        "per_run": per_run,
        "H4_consistent_across_cutoffs": h4,
        "verdict": verdict,
        "promotion_allowed": False,
    }


def main() -> int:
    import json
    from datetime import datetime

    result = run_house_trial_on_runs(
        ["studio_oos_005_*", "studio_oos_006_*"],
        Path("experiments/runs/regime_index_001_20260610/regime_history.csv"),
    )
    out_dir = Path("experiments/runs") / f"house_trial_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "house_trial_result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("ARTIFACTS:", out_dir)
    print("VERDICT:", result["verdict"])
    print(json.dumps(result["per_run"], indent=2, default=str)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
