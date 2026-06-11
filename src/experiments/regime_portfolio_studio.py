"""Regime Portfolio Studio engine.

Per ogni regime di mercato: filtra i componenti ammessi dal router, trova il
basket migliore con la ricerca governata esistente, poi compone un portfolio
regime-switching che usa il basket del regime attivo in ogni periodo.

Tutto resta diagnostico/proxy: nessuna promozione, nessun claim live. La
modalita' di aggregazione (compounded vs additive) viene rilevata onestamente
da ``_aggregate_curve`` e propagata in ogni summary.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.experiments.workbench_portfolio_engine import (
    _aggregate_curve,
    build_component_return_matrix,
    run_portfolio_diagnostic,
)

ALLOWED_POSTURES = {"ALLOW_PROXY", "REDUCE", "RISK_OVERLAY"}

POSTURE_MULTIPLIER = {
    "BLOCK": 0.0,
    "OBSERVE_ONLY": 0.0,
    "REDUCE": 0.5,
    "ALLOW_PROXY": 1.0,
    "RISK_OVERLAY": 1.0,
}


def component_strategy_family(component: dict[str, Any]) -> str:
    """Classifica la famiglia strategica dal template/nome (best effort)."""

    template = str(component.get("template", "")).lower()
    strategy_name = str(component.get("strategy_name", "")).lower()
    haystack = f"{template} {strategy_name}"
    if "regime" in haystack:
        return "Regime Risk Engine"
    if "dollar" in haystack:
        return "Dollar-Bar Microstructure"
    if "orb" in haystack or "9:30" in haystack or "opening range" in haystack:
        return "9:30 AM ORB"
    if any(token in haystack for token in ("catalyst", "pead", "form 4", "pdufa", "13d", "sec", "insider")):
        return "Event Catalyst"
    if any(token in haystack for token in ("mean reversion", "reversion", "gaprev", "lowvol")):
        return "Mean Reversion"
    if any(token in haystack for token in ("momentum", "xmom")):
        return "Momentum"
    return "Mean Reversion"


def regime_allowed_components(
    components: list[dict[str, Any]],
    router_matrix: pd.DataFrame,
    regime: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split components into (allowed, blocked) for one regime."""

    if router_matrix.empty:
        return list(components), []
    rows = router_matrix[router_matrix["regime_label"].astype(str).eq(str(regime))]
    posture_by_family = {str(row["strategy_family"]): str(row["posture"]) for _, row in rows.iterrows()}
    allowed: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for component in components:
        family = component_strategy_family(component)
        posture = posture_by_family.get(family, "OBSERVE_ONLY")
        enriched = {
            **component,
            "regime_family": family,
            "regime_posture": posture,
            "regime_weight_multiplier": POSTURE_MULTIPLIER.get(posture, 0.0),
        }
        (allowed if posture in ALLOWED_POSTURES else blocked).append(enriched)
    return allowed, blocked


def optimize_basket_for_regime(
    components: list[dict[str, Any]],
    router_matrix: pd.DataFrame,
    regime: str,
    *,
    policy: str = "equal_weight",
) -> dict[str, Any]:
    """Best governed basket among the components allowed in this regime."""

    allowed, blocked = regime_allowed_components(components, router_matrix, regime)
    if len(allowed) < 2:
        return {
            "regime": regime,
            "status": "NOT_ENOUGH_ALLOWED_COMPONENTS",
            "allowed_count": len(allowed),
            "blocked_count": len(blocked),
            "basket_component_ids": [str(c.get("component_id")) for c in allowed],
            "weights": {str(c.get("component_id")): 1.0 / max(len(allowed), 1) for c in allowed},
            "summary": {},
            "promotion_allowed": False,
        }
    diagnostic = run_portfolio_diagnostic(allowed, policy=policy)
    search = diagnostic.get("portfolio_search", {})
    if search.get("search_performed") and search.get("best_basket_component_ids"):
        basket_ids = [str(item) for item in search["best_basket_component_ids"]]
        summary = dict(search.get("best_summary", {}))
        weights = {component_id: 1.0 / len(basket_ids) for component_id in basket_ids}
    else:
        allocation = diagnostic.get("allocation", [])
        basket_ids = [str(row["component_id"]) for row in allocation]
        weights = {str(row["component_id"]): float(row["weight"]) for row in allocation}
        summary = dict(diagnostic.get("summary", {}))
    return {
        "regime": regime,
        "status": "BASKET_SELECTED_DIAGNOSTIC_ONLY",
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "basket_component_ids": basket_ids,
        "weights": weights,
        "summary": summary,
        "promotion_allowed": False,
    }


def regime_label_by_period(periods: pd.Index, regime_map: pd.DataFrame, *, default: str = "RANGE_NORMAL") -> dict[str, str]:
    """Majority regime per date, forward-filled to each period label."""

    if regime_map.empty or not {"date", "regime_label"}.issubset(regime_map.columns):
        return {str(period): default for period in periods}
    frame = regime_map.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date", "regime_label"])
    if frame.empty:
        return {str(period): default for period in periods}
    majority = (
        frame.groupby(["date", "regime_label"], as_index=False)
        .size()
        .sort_values(["date", "size", "regime_label"], ascending=[True, False, True])
        .drop_duplicates("date")
        .sort_values("date")
    )
    dates = majority["date"].tolist()
    labels = majority["regime_label"].astype(str).tolist()
    mapping: dict[str, str] = {}
    for period in periods:
        parsed = pd.to_datetime(str(period), errors="coerce")
        if pd.isna(parsed):
            mapping[str(period)] = labels[-1]
            continue
        position = pd.Index(dates).searchsorted(parsed, side="right") - 1
        mapping[str(period)] = labels[position] if position >= 0 else labels[0]
    return mapping


def compose_regime_switching_portfolio(
    components: list[dict[str, Any]],
    baskets_by_regime: dict[str, dict[str, Any]],
    regime_map: pd.DataFrame,
) -> dict[str, Any]:
    """Replay: in ogni periodo usa il basket del regime attivo.

    Confronta il path dinamico con la baseline statica equal-weight su tutti i
    componenti vivi. Aggregazione onesta via ``_aggregate_curve``.
    """

    matrix = build_component_return_matrix(components)
    if matrix.empty:
        return {"status": "NO_RETURN_STREAMS", "summary": {}, "curves": pd.DataFrame(), "promotion_allowed": False}
    regime_of = regime_label_by_period(matrix.index, regime_map)
    dynamic_returns: list[float] = []
    active_regimes: list[str] = []
    used_components: list[int] = []
    for period in matrix.index:
        regime = regime_of[str(period)]
        basket = baskets_by_regime.get(regime, {})
        weights = basket.get("weights", {})
        alive = {
            component_id: weight
            for component_id, weight in weights.items()
            if component_id in matrix.columns and pd.notna(matrix.loc[period, component_id]) and weight > 0
        }
        total = sum(alive.values())
        if total > 0:
            value = sum(float(matrix.loc[period, cid]) * (w / total) for cid, w in alive.items())
        else:
            value = 0.0
        dynamic_returns.append(value)
        active_regimes.append(regime)
        used_components.append(len(alive))
    dynamic = pd.Series(dynamic_returns, index=matrix.index, dtype=float)
    static = matrix.mean(axis=1, skipna=True).fillna(0.0)
    joint = pd.concat([dynamic, static])
    _, mode = _aggregate_curve(joint)
    if mode == "compounded":
        dynamic_curve = (1.0 + dynamic.fillna(0.0)).cumprod() - 1.0
        static_curve = (1.0 + static.fillna(0.0)).cumprod() - 1.0
    else:
        dynamic_curve = dynamic.fillna(0.0).cumsum()
        static_curve = static.fillna(0.0).cumsum()
    dynamic_dd = dynamic_curve - dynamic_curve.cummax()
    static_dd = static_curve - static_curve.cummax()
    curves = pd.DataFrame(
        {
            "period": [str(p) for p in matrix.index],
            "regime": active_regimes,
            "alive_components": used_components,
            "dynamic": dynamic_curve.to_numpy(),
            "static": static_curve.to_numpy(),
            "dynamic_drawdown": dynamic_dd.to_numpy(),
            "static_drawdown": static_dd.to_numpy(),
        }
    )
    usage = curves.groupby("regime", as_index=False).agg(periods=("regime", "size"), avg_components=("alive_components", "mean"))
    summary = {
        "aggregation_mode": mode,
        "period_count": int(len(matrix)),
        "component_count": int(matrix.shape[1]),
        "dynamic_total": round(float(dynamic_curve.iloc[-1]), 8),
        "static_total": round(float(static_curve.iloc[-1]), 8),
        "dynamic_vs_static_delta": round(float(dynamic_curve.iloc[-1] - static_curve.iloc[-1]), 8),
        "dynamic_max_drawdown": round(float(dynamic_dd.min()), 8),
        "static_max_drawdown": round(float(static_dd.min()), 8),
    }
    return {
        "status": "REGIME_STUDIO_DIAGNOSTIC_ONLY",
        "summary": summary,
        "curves": curves,
        "regime_usage": usage,
        "promotion_allowed": False,
        "provider_query_performed": False,
        "backtest_performed": False,
    }


def run_regime_studio(
    components: list[dict[str, Any]],
    router_matrix: pd.DataFrame,
    regime_map: pd.DataFrame,
    *,
    policy: str = "equal_weight",
) -> dict[str, Any]:
    """Pipeline completa: best basket per ogni regime + composizione finale."""

    regimes = (
        sorted(router_matrix["regime_label"].astype(str).unique())
        if not router_matrix.empty and "regime_label" in router_matrix.columns
        else []
    )
    baskets = {regime: optimize_basket_for_regime(components, router_matrix, regime, policy=policy) for regime in regimes}
    composition = compose_regime_switching_portfolio(components, baskets, regime_map)
    return {
        "status": "REGIME_STUDIO_DIAGNOSTIC_ONLY",
        "baskets_by_regime": baskets,
        "composition": composition,
        "promotion_allowed": False,
    }
