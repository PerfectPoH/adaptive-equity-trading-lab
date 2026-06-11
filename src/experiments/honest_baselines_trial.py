"""TRIAL-STUDIO-OOS-008: baseline oneste + permutation test del routing.

Risposta operativa all'audit esterno del 2026-06-11 (B1: cost-tier artifact;
B2: duplicati nel pool). Tre baseline oneste e il test che l'audit indica
come l'unico capace di dimostrare skill di regime:

  - static_cost_matched : equal-weight SOLO componenti <=100bps (dedup)
  - unconditional_top5  : top-5 Sharpe in-sample SENZA routing, fisso in OOS
  - permutation test    : 200 shift circolari delle label di regime ->
                          p-value empirico del delta dynamic vs unconditional

Gates: S1 dynamic > static_cost_matched; S2 dynamic > unconditional_top5;
S3 permutation p <= 0.05. Diagnostico: nessuna promozione.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.experiments.studio_oos_validation import (
    OosConfig,
    _components_from_matrix,
    _vol_normalized_matrix,
    preregistered_rule_baskets,
    _replay,
)
from src.experiments.regime_portfolio_studio import regime_label_by_period
from src.experiments.workbench_portfolio_engine import (
    _aggregate_curve,
    _component_return_series,
    build_component_return_matrix,
)
from src.validation.deflated_sharpe import sample_sharpe_ratio


@dataclass(frozen=True)
class HonestBaselinesConfig:
    cutoff: str = "2025-01-01"
    top_k: int = 5
    cost_matched_max_bps: int = 100
    permutations: int = 200
    permutation_seed: int = 20260611
    alpha: float = 0.05


def dedup_components(components: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Rimuove i componenti con stream di ritorni identico (audit B2)."""

    seen: dict[str, str] = {}
    kept: list[dict[str, Any]] = []
    removed = 0
    for component in components:
        series = _component_return_series(component)
        if series.empty:
            continue
        digest = hashlib.sha256(pd.util.hash_pandas_object(series.round(10)).values.tobytes()).hexdigest()
        if digest in seen:
            removed += 1
            continue
        seen[digest] = str(component.get("component_id"))
        kept.append(component)
    return kept, removed


def _curve_total(returns: pd.Series) -> tuple[float, str]:
    curve, mode = _aggregate_curve(returns)
    return (float(curve.iloc[-1]) if len(curve) else 0.0), mode


def _weighted_oos_mean(matrix: pd.DataFrame, ids: list[str]) -> pd.Series:
    cols = [c for c in ids if c in matrix.columns]
    if not cols:
        return pd.Series(0.0, index=matrix.index)
    return matrix[cols].mean(axis=1, skipna=True).fillna(0.0)


def run_honest_baselines_trial(
    components: list[dict[str, Any]],
    router_matrix: pd.DataFrame,
    regime_map: pd.DataFrame,
    config: HonestBaselinesConfig | None = None,
) -> dict[str, Any]:
    cfg = config or HonestBaselinesConfig()
    cutoff = pd.Timestamp(cfg.cutoff)

    deduped, removed = dedup_components(components)
    matrix = build_component_return_matrix(deduped)
    dates = pd.to_datetime(matrix.index, errors="coerce")
    oos_cfg = OosConfig(cutoff=cfg.cutoff, vol_normalize=True)
    matrix, factors, excluded = _vol_normalized_matrix(matrix, dates, cutoff, oos_cfg)
    pre = matrix[(dates.notna()) & (dates < cutoff)]
    oos = matrix[(dates.notna()) & (dates >= cutoff)]

    in_sample = _components_from_matrix(pre, deduped)
    baskets = preregistered_rule_baskets(in_sample, pre, router_matrix, top_k=cfg.top_k)
    regime_of = regime_label_by_period(oos.index, regime_map)
    dynamic, _, _ = _replay(oos, baskets, regime_of)
    dynamic_total, mode = _curve_total(dynamic)

    # baseline 1: static legacy (tutti) - per riferimento
    static_all = oos.mean(axis=1, skipna=True).fillna(0.0)
    static_all_total, _ = _curve_total(static_all)
    # baseline 2: static a parita' di costi (<=100bps)
    cost_by_id = {str(c.get("component_id")): int(c.get("cost_bps", 0) or 0) for c in deduped}
    low_cost_ids = [cid for cid in matrix.columns if cost_by_id.get(str(cid), 999) <= cfg.cost_matched_max_bps]
    static_cost = _weighted_oos_mean(oos, low_cost_ids)
    static_cost_total, _ = _curve_total(static_cost)
    # baseline 3: top-5 unconditional Sharpe in-sample (niente routing)
    sharpe_by_id = {
        str(c): sample_sharpe_ratio(pre[c].dropna().to_numpy())
        for c in pre.columns
        if pre[c].notna().sum() >= 60
    }
    uncond_ids = [cid for cid, _ in sorted(sharpe_by_id.items(), key=lambda kv: kv[1], reverse=True)[: cfg.top_k]]
    uncond = _weighted_oos_mean(oos, uncond_ids)
    uncond_total, _ = _curve_total(uncond)

    # permutation test: shift circolari della sequenza di regimi
    rng = np.random.default_rng(cfg.permutation_seed)
    period_keys = [str(p) for p in oos.index]
    regime_sequence = [regime_of[k] for k in period_keys]
    permuted_totals: list[float] = []
    n = len(regime_sequence)
    for _ in range(cfg.permutations):
        offset = int(rng.integers(1, n - 1))
        shifted = {k: regime_sequence[(i + offset) % n] for i, k in enumerate(period_keys)}
        perm_dynamic, _, _ = _replay(oos, baskets, shifted)
        total, _ = _curve_total(perm_dynamic)
        permuted_totals.append(total)
    permuted = np.asarray(permuted_totals)
    # Convenzione (1+count)/(n+1): mai p=0 spuri con n permutazioni finite.
    p_value = float((1 + int((permuted >= dynamic_total).sum())) / (len(permuted) + 1))

    # Ipotesi MEMBERSHIP separata dal timing (suggerimento audit follow-up):
    # blend statico dei basket per-regime (media dei pesi, MAI switching).
    blend_weights: dict[str, float] = {}
    for basket in baskets.values():
        for cid, w in basket.get("weights", {}).items():
            blend_weights[cid] = blend_weights.get(cid, 0.0) + w
    total_w = sum(blend_weights.values())
    membership_ids = list(blend_weights)
    if total_w > 0 and membership_ids:
        cols = [c for c in membership_ids if c in oos.columns]
        weights_series = pd.Series({c: blend_weights[c] / total_w for c in cols})
        aligned = oos[cols]
        active = aligned.notna().astype(float).mul(weights_series, axis=1).sum(axis=1)
        membership = aligned.mul(weights_series, axis=1).sum(axis=1, skipna=True).divide(
            active.where(active > 0)
        ).fillna(0.0)
    else:
        membership = pd.Series(0.0, index=oos.index)
    membership_total, _ = _curve_total(membership)

    gates = {
        "S1_beats_cost_matched_static": dynamic_total > static_cost_total,
        "S2_beats_unconditional_top5": dynamic_total > uncond_total,
        "S3_permutation_significant": p_value <= cfg.alpha,
    }
    return {
        "trial_id": "TRIAL-STUDIO-OOS-008",
        "status": "HONEST_BASELINES_TRIAL_COMPLETE",
        "pool": {
            "components_after_dedup": int(matrix.shape[1]),
            "duplicates_removed": removed,
            "low_cost_components": len(low_cost_ids),
            "vol_norm_excluded": len(excluded),
        },
        "aggregation_mode": mode,
        "results": {
            "dynamic_regime_routed": round(dynamic_total, 6),
            "static_all_legacy": round(static_all_total, 6),
            "static_cost_matched": round(static_cost_total, 6),
            "unconditional_top5": round(uncond_total, 6),
            "membership_blend_static": round(membership_total, 6),
            "routing_delta_vs_unconditional": round(dynamic_total - uncond_total, 6),
            "timing_delta_vs_membership": round(dynamic_total - membership_total, 6),
        },
        "permutation": {
            "n": cfg.permutations,
            "p_value": round(p_value, 4),
            "permuted_mean": round(float(permuted.mean()), 6),
            "permuted_p95": round(float(np.quantile(permuted, 0.95)), 6),
        },
        "gates": gates,
        "verdict": "ROUTING_SKILL_" + ("CONFIRMED" if all(gates.values()) else "NOT_CONFIRMED__" + "_".join(k.split("_")[0] for k, v in gates.items() if not v)),
        "promotion_allowed": False,
        "unconditional_top5_ids": uncond_ids,
    }


def main() -> int:
    import argparse
    import json
    from datetime import datetime
    from pathlib import Path
    import sys

    repo = Path(__file__).resolve().parents[2]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from dashboard.lab_dashboard_data import (
        build_strategy_factory_components,
        load_dashboard_payload,
        load_portfolio_lab_components,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--extend-streams", action="store_true", help="RISK-044: estende gli stream con dati freschi (causale)")
    args = parser.parse_args()

    components = load_portfolio_lab_components(limit=60) + build_strategy_factory_components(max_variants=48)
    extension_coverage = None
    if args.extend_streams:
        from src.experiments.stream_extension import component_recipe, extend_components, refresh_panel

        symbols: set[str] = set()
        for component in components:
            recipe = component_recipe(component)
            if recipe:
                symbols.update(recipe.symbols)
        print(f"RISK-044: refresh panel per {len(symbols)} simboli...", flush=True)
        panels, panel_status = refresh_panel(symbols)
        stale = [s for s, st in panel_status.items() if st != "ok"]
        if stale:
            print(f"RISK-044: simboli stale/no_data (regola delisting attiva): {stale}", flush=True)
        components, extension_coverage = extend_components(components, panels, panel_status)
        print(f"RISK-044 coverage: {extension_coverage}", flush=True)
    payload = load_dashboard_payload(Path("."))
    result = run_honest_baselines_trial(components, payload["strategy_regime_router"]["matrix"], payload["regime_map"])
    if extension_coverage is not None:
        result["stream_extension_coverage"] = extension_coverage
    out_dir = Path("experiments/runs") / f"honest_baselines_008_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("ARTIFACTS:", out_dir)
    print("VERDICT:", result["verdict"])
    print(json.dumps({k: result[k] for k in ("pool", "results", "permutation", "gates")}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
