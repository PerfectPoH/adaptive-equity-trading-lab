"""TRIAL-STUDIO-OOS-001: validazione out-of-sample del Regime Portfolio Studio.

Domanda: la selezione per-regime dell'engine generalizza su dati mai visti?

Protocollo (preregistrato nel report vault):
  1. Gli stream dei componenti vengono TRONCATI al cutoff (default 2025-01-01).
  2. ``run_regime_studio`` sceglie i basket per regime SOLO sui dati pre-cutoff.
  3. La ricetta congelata viene replayata sul segmento OOS (cutoff -> fine).
  4. Gate: dynamic vs static OOS, ex-top3 sign flip, DSR con trial count
     reale della ricerca (prima volta che la gate dormiente viene collegata).

Tutto resta diagnostico su stream proxy: nessuna promozione. Il verdetto
parla dell'ENGINE (capacita' di selezione), non di un edge tradabile.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.experiments.regime_portfolio_studio import (
    regime_allowed_components,
    regime_label_by_period,
    run_regime_studio,
)
from src.experiments.workbench_portfolio_engine import (
    _aggregate_curve,
    _component_return_series,
    build_component_return_matrix,
)
from src.validation.deflated_sharpe import deflated_sharpe_ratio_from_returns, sample_sharpe_ratio


@dataclass(frozen=True)
class OosConfig:
    trial_id: str = "TRIAL-STUDIO-OOS-001"
    cutoff: str = "2025-01-01"
    policy: str = "equal_weight"
    min_oos_periods: int = 100
    dsr_confidence: float = 0.95
    capital_exposure: float = 0.10
    capital_clip: float = 0.50
    # Normalizzazione a volatilita' unitaria: i fattori di scala sono
    # calcolati SOLO sull'in-sample (niente leak), poi applicati a tutto.
    vol_normalize: bool = False
    target_vol: float = 0.01
    min_in_sample_periods: int = 60
    max_scale: float = 100.0
    # "search" = ricerca governata (multiplicita' alta, 60 candidati);
    # "rule"   = regola preregistrata fissa: top-k Sharpe in-sample per
    #            regime, equal weight, ZERO ricerca.
    selection_mode: str = "search"
    rule_top_k: int = 5


def truncate_components(components: list[dict[str, Any]], cutoff: pd.Timestamp) -> list[dict[str, Any]]:
    """Copy components keeping only the stream strictly before the cutoff."""

    truncated: list[dict[str, Any]] = []
    for component in components:
        series = _component_return_series(component)
        if series.empty:
            continue
        dates = pd.to_datetime(series.index, errors="coerce")
        keep = series[(dates.notna()) & (dates < cutoff)]
        if keep.empty:
            continue
        clone = dict(component)
        clone["inline_returns"] = [
            {"period": str(period), "net_return": float(value)} for period, value in keep.items()
        ]
        clone["trade_list_path"] = ""
        clone["equity_curve_path"] = ""
        truncated.append(clone)
    return truncated


def _vol_normalized_matrix(
    matrix: pd.DataFrame,
    dates: pd.DatetimeIndex,
    cutoff: pd.Timestamp,
    cfg: "OosConfig",
) -> tuple[pd.DataFrame, dict[str, float], list[str]]:
    """Scale each component to ``target_vol`` using IN-SAMPLE std only."""

    pre = matrix[(dates.notna()) & (dates < cutoff)]
    factors: dict[str, float] = {}
    excluded: list[str] = []
    for column in matrix.columns:
        series = pre[column].dropna()
        if len(series) < cfg.min_in_sample_periods:
            excluded.append(str(column))
            continue
        std = float(series.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            excluded.append(str(column))
            continue
        factors[str(column)] = float(min(cfg.target_vol / std, cfg.max_scale))
    kept = [c for c in matrix.columns if str(c) in factors]
    normalized = matrix[kept].mul(pd.Series(factors), axis=1)
    return normalized, factors, excluded


def _components_from_matrix(
    matrix_slice: pd.DataFrame,
    components: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Clone components replacing streams with the given matrix columns."""

    by_id = {str(c.get("component_id")): c for c in components}
    clones: list[dict[str, Any]] = []
    for column in matrix_slice.columns:
        base = by_id.get(str(column))
        if base is None:
            continue
        series = matrix_slice[column].dropna()
        if series.empty:
            continue
        clone = dict(base)
        clone["inline_returns"] = [
            {"period": str(period), "net_return": float(value)} for period, value in series.items()
        ]
        clone["trade_list_path"] = ""
        clone["equity_curve_path"] = ""
        clones.append(clone)
    return clones


def _replay(
    matrix: pd.DataFrame,
    baskets_by_regime: dict[str, dict[str, Any]],
    regime_of: dict[str, str],
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """Dynamic (frozen baskets) e static (equal weight) sullo stesso indice."""

    dynamic_values: list[float] = []
    contribution: dict[str, float] = {}
    for period in matrix.index:
        regime = regime_of[str(period)]
        weights = baskets_by_regime.get(regime, {}).get("weights", {})
        alive = {
            cid: w
            for cid, w in weights.items()
            if cid in matrix.columns and pd.notna(matrix.loc[period, cid]) and w > 0
        }
        total = sum(alive.values())
        value = 0.0
        if total > 0:
            for cid, w in alive.items():
                part = float(matrix.loc[period, cid]) * (w / total)
                value += part
                contribution[cid] = contribution.get(cid, 0.0) + part
        dynamic_values.append(value)
    dynamic = pd.Series(dynamic_values, index=matrix.index, dtype=float)
    static = matrix.mean(axis=1, skipna=True).fillna(0.0)
    contrib = (
        pd.DataFrame({"component_id": list(contribution), "oos_contribution": list(contribution.values())})
        .sort_values("oos_contribution", ascending=False)
        .reset_index(drop=True)
    )
    return dynamic, static, contrib


def _capital_simulation(returns: pd.Series, exposure: float, clip: float) -> dict[str, float]:
    """Equity % illustrativa: esposizione fissa, clip dichiarato sugli estremi."""

    clipped = returns.clip(-clip, clip)
    clipped_count = int((returns != clipped).sum())
    equity = (1.0 + exposure * clipped.fillna(0.0)).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return {
        "final_return_pct": round(float(equity.iloc[-1] - 1.0) * 100.0, 4),
        "max_drawdown_pct": round(float(drawdown.min()) * 100.0, 4),
        "exposure": exposure,
        "clip": clip,
        "clipped_periods": clipped_count,
    }


def preregistered_rule_baskets(
    in_sample_components: list[dict[str, Any]],
    pre_matrix: pd.DataFrame,
    router_matrix: pd.DataFrame,
    *,
    top_k: int,
) -> dict[str, dict[str, Any]]:
    """Regola FISSA, zero ricerca: per ogni regime prendi i top-k componenti
    ammessi per Sharpe in-sample, pesi uguali. Multiplicita' = 1 regola."""

    regimes = (
        sorted(router_matrix["regime_label"].astype(str).unique())
        if not router_matrix.empty and "regime_label" in router_matrix.columns
        else []
    )
    sharpe_by_id: dict[str, float] = {}
    for column in pre_matrix.columns:
        series = pre_matrix[column].dropna()
        if len(series) >= 60:
            sharpe_by_id[str(column)] = sample_sharpe_ratio(series.to_numpy())
    baskets: dict[str, dict[str, Any]] = {}
    for regime in regimes:
        allowed, blocked = regime_allowed_components(in_sample_components, router_matrix, regime)
        ranked = sorted(
            (c for c in allowed if str(c.get("component_id")) in sharpe_by_id),
            key=lambda c: sharpe_by_id[str(c.get("component_id"))],
            reverse=True,
        )[: max(top_k, 1)]
        ids = [str(c.get("component_id")) for c in ranked]
        baskets[regime] = {
            "regime": regime,
            "status": "PREREGISTERED_RULE_TOP_K_SHARPE",
            "allowed_count": len(allowed),
            "blocked_count": len(blocked),
            "basket_component_ids": ids,
            "weights": {cid: 1.0 / len(ids) for cid in ids} if ids else {},
            "summary": {"selection_rule": f"top_{top_k}_in_sample_sharpe_equal_weight"},
            "promotion_allowed": False,
        }
    return baskets


def run_studio_oos_validation(
    components: list[dict[str, Any]],
    router_matrix: pd.DataFrame,
    regime_map: pd.DataFrame,
    config: OosConfig | None = None,
) -> dict[str, Any]:
    cfg = config or OosConfig()
    cutoff = pd.Timestamp(cfg.cutoff)

    # 0. matrice completa (e normalizzazione vol-unitaria se richiesta)
    full_matrix = build_component_return_matrix(components)
    full_dates = pd.to_datetime(full_matrix.index, errors="coerce")
    normalization: dict[str, Any] = {"enabled": bool(cfg.vol_normalize)}
    if cfg.vol_normalize:
        full_matrix, factors, excluded = _vol_normalized_matrix(full_matrix, full_dates, cutoff, cfg)
        normalization.update(
            {
                "target_vol": cfg.target_vol,
                "normalized_components": len(factors),
                "excluded_components": len(excluded),
                "max_abs_scaled_return": round(float(full_matrix.abs().max().max()), 6) if not full_matrix.empty else 0.0,
            }
        )

    # 1-2. selezione congelata sui soli dati pre-cutoff
    pre_matrix = full_matrix[(full_dates.notna()) & (full_dates < cutoff)]
    if cfg.vol_normalize:
        in_sample = _components_from_matrix(pre_matrix, components)
    else:
        in_sample = truncate_components(components, cutoff)
    if cfg.selection_mode == "rule":
        baskets = preregistered_rule_baskets(in_sample, pre_matrix, router_matrix, top_k=cfg.rule_top_k)
        trial_count = 2.0  # minimo tecnico DSR: una regola fissa, zero ricerca
    else:
        studio = run_regime_studio(in_sample, router_matrix, regime_map, policy=cfg.policy)
        baskets = studio["baskets_by_regime"]
        trial_count = 0.0
        for basket in baskets.values():
            summary = basket.get("summary", {}) or {}
            trial_count += float(summary.get("evaluated_candidate_count", 0) or 0)
        if trial_count <= 0:
            trial_count = float(max(len(baskets), 1) * 10)  # fallback conservativo

    # 3. replay OOS sugli stream completi (stessa scala della selezione)
    matrix = full_matrix
    dates = full_dates
    oos_matrix = matrix[(dates.notna()) & (dates >= cutoff)]
    if len(oos_matrix) < cfg.min_oos_periods:
        return {"status": "INSUFFICIENT_OOS_PERIODS", "oos_periods": int(len(oos_matrix)), "promotion_allowed": False}
    regime_of = regime_label_by_period(oos_matrix.index, regime_map)
    dynamic, static, contrib = _replay(oos_matrix, baskets, regime_of)

    dynamic_curve, mode = _aggregate_curve(dynamic)
    static_curve, _ = _aggregate_curve(pd.concat([static, dynamic]).iloc[: len(static)])  # stessa modalita'
    if mode == "additive":
        static_curve = static.fillna(0.0).cumsum()
    dynamic_dd = dynamic_curve - dynamic_curve.cummax()

    # 4a. ex-top3: rimuovi i 3 componenti che hanno contribuito di piu'
    top3 = contrib.head(3)["component_id"].tolist()
    reduced_baskets = {
        regime: {
            **basket,
            "weights": {cid: w for cid, w in basket.get("weights", {}).items() if cid not in top3},
        }
        for regime, basket in baskets.items()
    }
    dynamic_ex3, _, _ = _replay(oos_matrix, reduced_baskets, regime_of)
    ex3_total = float(dynamic_ex3.sum())
    sign_flip = (float(dynamic.sum()) > 0) != (ex3_total > 0) if float(dynamic.sum()) != 0 else False

    # 4b. DSR sulla serie OOS giornaliera, deflazionata dai trial della ricerca
    component_sharpes = [
        sample_sharpe_ratio(matrix[c][dates < cutoff].dropna().to_numpy())
        for c in matrix.columns
        if matrix[c][dates < cutoff].notna().sum() >= 60
    ]
    sharpe_std = float(np.nanstd(np.asarray(component_sharpes, dtype=float), ddof=1)) if len(component_sharpes) > 2 else 1.0
    sharpe_std = max(sharpe_std, 1e-6)
    dsr = deflated_sharpe_ratio_from_returns(
        dynamic.fillna(0.0).to_numpy(),
        trial_count=max(trial_count, 2.0),
        sharpe_std=sharpe_std,
        confidence_threshold=cfg.dsr_confidence,
    )
    dsr_by_trials: dict[str, float] = {}
    max_trials_with_pass = 0
    for probe in (2, 3, 5, 10, 20, 40, 60):
        probe_result = deflated_sharpe_ratio_from_returns(
            dynamic.fillna(0.0).to_numpy(),
            trial_count=float(probe),
            sharpe_std=sharpe_std,
            confidence_threshold=cfg.dsr_confidence,
        )
        dsr_by_trials[str(probe)] = round(probe_result.dsr, 6)
        if probe_result.passed:
            max_trials_with_pass = probe

    capital = _capital_simulation(dynamic, cfg.capital_exposure, cfg.capital_clip)

    dynamic_total = float(dynamic_curve.iloc[-1])
    static_total = float(static_curve.iloc[-1])
    beats_static = dynamic_total > static_total
    verdict_parts = []
    verdict_parts.append("OOS_POSITIVE" if dynamic_total > 0 else "OOS_NEGATIVE")
    verdict_parts.append("BEATS_STATIC" if beats_static else "UNDER_STATIC")
    verdict_parts.append("OUTLIER_FRAGILE" if sign_flip else "OUTLIER_ROBUST")
    verdict_parts.append("DSR_PASS" if dsr.passed else "DSR_FAIL")
    verdict = "__".join(verdict_parts)

    curves = pd.DataFrame(
        {
            "period": [str(p) for p in oos_matrix.index],
            "regime": [regime_of[str(p)] for p in oos_matrix.index],
            "dynamic": dynamic_curve.to_numpy(),
            "static": static_curve.to_numpy(),
            "dynamic_drawdown": dynamic_dd.to_numpy(),
        }
    )
    return {
        "status": "STUDIO_OOS_VALIDATION_COMPLETE",
        "trial_id": cfg.trial_id,
        "normalization": normalization,
        "config": {
            "cutoff": str(cfg.cutoff),
            "policy": cfg.policy,
            "component_count": int(matrix.shape[1]),
            "in_sample_periods": int((dates < cutoff).sum()),
            "oos_periods": int(len(oos_matrix)),
        },
        "summary": {
            "aggregation_mode": mode,
            "dynamic_total_oos": round(dynamic_total, 6),
            "static_total_oos": round(static_total, 6),
            "dynamic_vs_static_delta": round(dynamic_total - static_total, 6),
            "dynamic_max_drawdown": round(float(dynamic_dd.min()), 6),
            "ex_top3_total": round(ex3_total, 6),
            "sign_flip_excluding_top_3": bool(sign_flip),
            "top3_components": top3,
        },
        "statistical_gate": {
            "observed_sharpe_daily": round(dsr.observed_sharpe, 6),
            "benchmark_sharpe": round(dsr.benchmark_sharpe, 6),
            "trial_count": trial_count,
            "sharpe_std_cross_section": round(sharpe_std, 6),
            "psr": round(dsr.psr, 6),
            "dsr": round(dsr.dsr, 6),
            "dsr_passed": bool(dsr.passed),
            "dsr_by_trial_count": dsr_by_trials,
            "multiplicity_budget": max_trials_with_pass,
            "selection_mode": cfg.selection_mode,
            "note": "multiplicity_budget = numero massimo di candidati cercati a cui il risultato reggerebbe la DSR.",
        },
        "capital_simulation_illustrative": capital,
        "baskets_frozen": {
            regime: {
                "components": basket.get("basket_component_ids", []),
                "allowed": basket.get("allowed_count"),
                "blocked": basket.get("blocked_count"),
            }
            for regime, basket in baskets.items()
        },
        "curves": curves,
        "verdict": verdict,
        "promotion_allowed": False,
        "provider_query_performed": False,
        "interpretation": (
            "Il verdetto riguarda la capacita' di selezione dell'engine su stream proxy, "
            "non un edge tradabile: i componenti restano strategie non validate singolarmente."
        ),
    }
