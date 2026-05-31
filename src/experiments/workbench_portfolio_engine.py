from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError


WORKBENCH_OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/USER-STRATEGY-WORKBENCH")
PORTFOLIO_OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/USER-STRATEGY-PORTFOLIOS")
FORBIDDEN_FLAGS = {"--paper", "--live", "--promote", "--provider-query", "--download-market-data"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str)) else False:
        return None
    return value


def load_workbench_portfolio_components(*, root: Path = Path("."), limit: int = 40) -> list[dict[str, Any]]:
    """Load saved Workbench dry-run artifacts as portfolio components."""

    output_root = Path(root) / WORKBENCH_OUTPUT_DIR
    if not output_root.exists():
        return []
    result_paths = sorted(
        output_root.glob("*/dry_run_result.json"),
        key=lambda path: (path.stat().st_mtime_ns, path.parent.name),
        reverse=True,
    )
    components: list[dict[str, Any]] = []
    for result_path in result_paths[:limit]:
        run_dir = result_path.parent
        result = _read_json(result_path)
        verdict = result.get("automatic_verdict", {})
        cost = result.get("cost_breakdown", {})
        warnings = result.get("bias_warnings", []) or []
        warning_ids = [str(row.get("warning_id", row.get("message", "UNKNOWN_WARNING"))) for row in warnings if isinstance(row, dict)]
        trade_path = run_dir / "trade_list.csv"
        equity_path = run_dir / "equity_curve.csv"
        trade_count = int(result.get("simulated_trades") or 0)
        if trade_count == 0 and trade_path.exists():
            trade_count = len(_safe_read_csv(trade_path))
        components.append(
            {
                "component_id": run_dir.name,
                "strategy_name": result.get("strategy_name", run_dir.name),
                "template": result.get("template", "UNKNOWN"),
                "analysis_mode": result.get("analysis_mode", "UNKNOWN"),
                "decision": verdict.get("decision", result.get("decision", "UNKNOWN")),
                "promotion_allowed": bool(verdict.get("promotion_allowed", False)),
                "bias_warnings": warning_ids,
                "trade_count": trade_count,
                "net_return_sum": float(cost.get("net_return_sum") or 0.0),
                "gross_return_sum": float(cost.get("gross_return_sum") or 0.0),
                "cost_bps": int(result.get("cost_bps") or cost.get("round_trip_cost_bps") or 0),
                "artifact_dir": str(run_dir),
                "trade_list_path": str(trade_path) if trade_path.exists() else "",
                "equity_curve_path": str(equity_path) if equity_path.exists() else "",
            }
        )
    return components


def build_component_return_matrix(components: list[dict[str, Any]]) -> pd.DataFrame:
    """Align saved component return streams into a common local diagnostic matrix."""

    series_by_component: dict[str, pd.Series] = {}
    for component in components:
        series = _component_return_series(component)
        if not series.empty:
            series_by_component[str(component["component_id"])] = series
    if not series_by_component:
        return pd.DataFrame()
    matrix = pd.DataFrame(series_by_component).fillna(0.0)
    return matrix.sort_index()


def _component_return_series(component: dict[str, Any]) -> pd.Series:
    inline_returns = component.get("inline_returns", [])
    if isinstance(inline_returns, list) and inline_returns:
        periods = [str(row.get("period", f"step-{index:05d}")) for index, row in enumerate(inline_returns, start=1) if isinstance(row, dict)]
        values = [float(row.get("net_return", 0.0) or 0.0) for row in inline_returns if isinstance(row, dict)]
        if periods and len(periods) == len(values):
            return pd.Series(values, index=periods).groupby(level=0).sum().sort_index()
    equity_value = str(component.get("equity_curve_path", ""))
    trade_value = str(component.get("trade_list_path", ""))
    equity_path = Path(equity_value) if equity_value else None
    trade_path = Path(trade_value) if trade_value else None
    if equity_path and equity_path.exists():
        equity = _safe_read_csv(equity_path)
        if {"date", "cumulative_net_return"}.issubset(equity.columns):
            frame = equity.copy()
            frame["period"] = pd.to_datetime(frame["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            if frame["period"].isna().all():
                frame["period"] = frame.get("step", pd.Series(range(1, len(frame) + 1))).map(lambda item: f"step-{int(item):05d}")
            cumulative = pd.to_numeric(frame["cumulative_net_return"], errors="coerce").fillna(0.0)
            returns = cumulative.diff().fillna(cumulative)
            return pd.Series(returns.to_numpy(), index=frame["period"]).groupby(level=0).sum().sort_index()
    if trade_path and trade_path.exists():
        trades = _safe_read_csv(trade_path)
        if "net_return" in trades.columns:
            date_column = "entry_date" if "entry_date" in trades.columns else "exit_date"
            if date_column in trades.columns:
                periods = pd.to_datetime(trades[date_column], errors="coerce").dt.strftime("%Y-%m-%d")
            else:
                periods = pd.Series([f"step-{index:05d}" for index in range(1, len(trades) + 1)])
            values = pd.to_numeric(trades["net_return"], errors="coerce").fillna(0.0)
            return pd.Series(values.to_numpy(), index=periods).groupby(level=0).sum().sort_index()
    return pd.Series(dtype=float)


def build_portfolio_allocation(
    components: list[dict[str, Any]],
    return_matrix: pd.DataFrame,
    *,
    policy: str = "equal_weight",
    max_component_weight: float = 0.60,
    max_rejected_weight: float = 0.20,
    max_convex_weight: float = 0.20,
) -> list[dict[str, Any]]:
    active = [component for component in components if str(component["component_id"]) in return_matrix.columns]
    if not active:
        return []
    policy = policy.lower().strip()
    if policy == "inverse_volatility":
        raw = _inverse_volatility_weights(active, return_matrix)
    elif policy == "sleeve_allocation":
        raw = _sleeve_weights(active, max_convex_weight=max_convex_weight)
    else:
        raw = {str(component["component_id"]): 1.0 / len(active) for component in active}
    caps = {}
    for component in active:
        component_id = str(component["component_id"])
        cap = max_component_weight
        if str(component.get("decision", "")).startswith("REJECTED"):
            cap = min(cap, max_rejected_weight)
        if _classify_sleeve(component) == "convex":
            cap = min(cap, max_convex_weight)
        caps[component_id] = max(0.0, cap)
    capped = _cap_and_redistribute(raw, caps)
    rows: list[dict[str, Any]] = []
    for component in active:
        component_id = str(component["component_id"])
        rows.append(
            {
                "component_id": component_id,
                "strategy_name": component.get("strategy_name", component_id),
                "template": component.get("template", "UNKNOWN"),
                "decision": component.get("decision", "UNKNOWN"),
                "sleeve": _classify_sleeve(component),
                "weight": round(float(capped.get(component_id, 0.0)), 8),
            }
        )
    return rows


def _inverse_volatility_weights(components: list[dict[str, Any]], return_matrix: pd.DataFrame) -> dict[str, float]:
    scores: dict[str, float] = {}
    for component in components:
        component_id = str(component["component_id"])
        volatility = float(return_matrix[component_id].std(ddof=0) or 0.0)
        scores[component_id] = 1.0 / max(volatility, 1e-6)
    total = sum(scores.values()) or 1.0
    return {component_id: score / total for component_id, score in scores.items()}


def _sleeve_weights(components: list[dict[str, Any]], *, max_convex_weight: float) -> dict[str, float]:
    by_sleeve: dict[str, list[str]] = {"core": [], "convex": [], "tactical": []}
    for component in components:
        by_sleeve[_classify_sleeve(component)].append(str(component["component_id"]))
    desired = {"core": 0.60, "convex": max_convex_weight, "tactical": max(0.0, 0.40 - max_convex_weight)}
    available = {sleeve: ids for sleeve, ids in by_sleeve.items() if ids}
    missing_weight = sum(weight for sleeve, weight in desired.items() if sleeve not in available)
    if missing_weight and available:
        redistribution_base = sum(desired[sleeve] for sleeve in available) or 1.0
        for sleeve in available:
            desired[sleeve] += missing_weight * (desired[sleeve] / redistribution_base)
    weights: dict[str, float] = {}
    for sleeve, ids in available.items():
        sleeve_weight = desired[sleeve]
        for component_id in ids:
            weights[component_id] = sleeve_weight / len(ids)
    total = sum(weights.values()) or 1.0
    return {component_id: weight / total for component_id, weight in weights.items()}


def _classify_sleeve(component: dict[str, Any]) -> str:
    template = str(component.get("template", "")).lower()
    if any(token in template for token in ("pdufa", "catalyst", "13d", "form 4", "insider", "sec")):
        return "convex"
    if any(token in template for token in ("orb", "9:30", "dollar", "momentum", "custom")):
        return "tactical"
    return "core"


def _cap_and_redistribute(weights: dict[str, float], caps: dict[str, float]) -> dict[str, float]:
    if not weights:
        return {}
    normalized_total = sum(max(0.0, value) for value in weights.values()) or 1.0
    result = {key: max(0.0, value) / normalized_total for key, value in weights.items()}
    for _ in range(len(result) + 2):
        excess = 0.0
        eligible: list[str] = []
        for key, value in list(result.items()):
            cap = caps.get(key, 1.0)
            if value > cap:
                excess += value - cap
                result[key] = cap
            elif value < cap:
                eligible.append(key)
        if excess <= 1e-12 or not eligible:
            break
        capacity = sum(caps.get(key, 1.0) - result[key] for key in eligible)
        if capacity <= 1e-12:
            break
        for key in eligible:
            room = caps.get(key, 1.0) - result[key]
            result[key] += excess * (room / capacity)
    total = sum(result.values())
    if total > 0 and abs(total - 1.0) > 1e-8:
        scalable = [key for key, value in result.items() if value < caps.get(key, 1.0)]
        if scalable:
            gap = 1.0 - total
            capacity = sum(caps.get(key, 1.0) - result[key] for key in scalable)
            if capacity > 0:
                for key in scalable:
                    result[key] += gap * ((caps.get(key, 1.0) - result[key]) / capacity)
    return result


def run_portfolio_diagnostic(
    components: list[dict[str, Any]],
    *,
    policy: str = "sleeve_allocation",
    max_component_weight: float = 0.60,
    max_rejected_weight: float = 0.20,
    max_convex_weight: float = 0.20,
) -> dict[str, Any]:
    matrix = build_component_return_matrix(components)
    allocation = build_portfolio_allocation(
        components,
        matrix,
        policy=policy,
        max_component_weight=max_component_weight,
        max_rejected_weight=max_rejected_weight,
        max_convex_weight=max_convex_weight,
    )
    weights = pd.Series({row["component_id"]: row["weight"] for row in allocation}, dtype=float)
    weighted_matrix = matrix.reindex(columns=weights.index, fill_value=0.0).mul(weights, axis=1) if not matrix.empty else pd.DataFrame()
    returns = weighted_matrix.sum(axis=1) if not weighted_matrix.empty else pd.Series(dtype=float)
    cumulative = returns.cumsum()
    running_peak = cumulative.cummax()
    drawdown = cumulative - running_peak
    contribution = weighted_matrix.sum(axis=0).sort_values(ascending=False) if not weighted_matrix.empty else pd.Series(dtype=float)
    correlation = matrix.reindex(columns=weights.index).corr().fillna(0.0) if len(weights) > 1 else pd.DataFrame()
    gate_panel = _build_gate_panel(components, matrix, allocation, returns, drawdown, contribution, correlation)
    final_decision = _build_final_decision(gate_panel, returns, components)
    high_correlation_pairs = _high_correlation_pairs(correlation, allocation)
    strategy_deduplication = _build_strategy_deduplication(components, allocation, correlation, contribution)
    portfolio_search = _build_portfolio_search(
        components,
        matrix,
        strategy_deduplication,
        policy=policy,
        max_component_weight=max_component_weight,
        max_rejected_weight=max_rejected_weight,
        max_convex_weight=max_convex_weight,
    )
    auto_clean = _build_auto_clean_plan(components, allocation, contribution, high_correlation_pairs)
    action_plan = _build_action_plan(gate_panel, allocation, contribution, high_correlation_pairs, final_decision)
    signature = _portfolio_signature(components, policy, max_component_weight, max_rejected_weight, max_convex_weight)
    equity_curve = [
        {
            "period": str(period),
            "portfolio_return": round(float(returns.loc[period]), 8),
            "cumulative_net_return": round(float(cumulative.loc[period]), 8),
            "drawdown": round(float(drawdown.loc[period]), 8),
        }
        for period in returns.index
    ]
    component_manifest = [
        {
            **{key: component[key] for key in ("component_id", "strategy_name", "template", "analysis_mode", "decision", "trade_count", "net_return_sum", "source") if key in component},
            "bias_warnings": ";".join(component.get("bias_warnings", [])),
            "weight": next((row["weight"] for row in allocation if row["component_id"] == component["component_id"]), 0.0),
            "sleeve": _classify_sleeve(component),
        }
        for component in components
        if str(component["component_id"]) in weights.index
    ]
    summary = {
        "portfolio_signature": signature,
        "component_count": len(allocation),
        "period_count": int(len(returns)),
        "policy": policy,
        "total_net_return": round(float(returns.sum() if not returns.empty else 0.0), 8),
        "max_drawdown": round(float(drawdown.min() if not drawdown.empty else 0.0), 8),
        "max_drawdown_pct": round(float((drawdown.min() if not drawdown.empty else 0.0) * 100.0), 4),
        "time_underwater_ratio": round(float((drawdown < 0).mean() if not drawdown.empty else 0.0), 8),
        "top_component_contribution": round(float((contribution.iloc[0] / max(contribution[contribution > 0].sum(), 1e-12)) if not contribution.empty and contribution.iloc[0] > 0 else 0.0), 8),
        "high_correlation_pair_count": len(high_correlation_pairs),
    }
    source_summary: dict[str, int] = {}
    for component in component_manifest:
        source = str(component.get("source", "saved_workbench"))
        source_summary[source] = source_summary.get(source, 0) + 1
    return {
        "portfolio_manifest": {
            "portfolio_id": "WORKBENCH-PORTFOLIO-001",
            "portfolio_signature": signature,
            "policy": policy,
            "max_component_weight": max_component_weight,
            "max_rejected_weight": max_rejected_weight,
            "max_convex_weight": max_convex_weight,
            "promotion_allowed": False,
            "provider_query_allowed": False,
            "paper_live_policy": "forbidden_from_portfolio_lab",
        },
        "summary": summary,
        "component_source_summary": source_summary,
        "components": component_manifest,
        "return_matrix": matrix.reset_index(names="period").to_dict("records") if not matrix.empty else [],
        "allocation": allocation,
        "equity_curve": equity_curve,
        "drawdown": [{"period": row["period"], "drawdown": row["drawdown"]} for row in equity_curve],
        "correlation_matrix": correlation.reset_index(names="component_id").to_dict("records") if not correlation.empty else [],
        "contribution": [{"component_id": key, "contribution": round(float(value), 8)} for key, value in contribution.items()],
        "high_correlation_pairs": high_correlation_pairs,
        "strategy_deduplication": strategy_deduplication,
        "portfolio_search": portfolio_search,
        "auto_clean": auto_clean,
        "action_plan": action_plan,
        "gate_panel": gate_panel,
        "final_decision": final_decision,
    }


def _build_gate_panel(
    components: list[dict[str, Any]],
    matrix: pd.DataFrame,
    allocation: list[dict[str, Any]],
    returns: pd.Series,
    drawdown: pd.Series,
    contribution: pd.Series,
    correlation: pd.DataFrame,
) -> list[dict[str, Any]]:
    warnings = sorted({warning for component in components for warning in component.get("bias_warnings", [])})
    component_count = len(allocation)
    allocated_ids = {str(row["component_id"]) for row in allocation}
    factory_generated_ids = sorted(
        str(component["component_id"])
        for component in components
        if str(component.get("component_id")) in allocated_ids
        and (
            str(component.get("source", "saved_workbench")) == "factory_generated"
            or "FACTORY_GENERATED_NOT_PREREGISTERED" in component.get("bias_warnings", [])
        )
    )
    positive_total = float(contribution[contribution > 0].sum()) if not contribution.empty else 0.0
    top_share = float(contribution.iloc[0] / positive_total) if positive_total > 0 and not contribution.empty else 0.0
    best_component = str(contribution.index[0]) if not contribution.empty else ""
    ex_best_return = _ex_best_return(matrix, allocation, best_component)
    avg_abs_corr = _average_abs_correlation(correlation)
    declared_cost_drag = _weighted_cost_drag(components, allocation)
    stressed_net = float(returns.sum() - declared_cost_drag * max(1, len(returns)) * 0.5) if not returns.empty else 0.0
    family_weights: dict[str, float] = {}
    for row in allocation:
        family_weights[row["sleeve"]] = family_weights.get(row["sleeve"], 0.0) + float(row["weight"])
    max_family_weight = max(family_weights.values()) if family_weights else 0.0
    return [
        {
            "gate": "data_contract_gate",
            "status": "WARN" if warnings else "PASS",
            "value": warnings or "no_component_bias_warnings",
            "detail": "Any proxy, active-only, PIT, or survivorship warning keeps the portfolio diagnostic-only.",
        },
        {
            "gate": "factory_generated_scope_gate",
            "status": "BLOCK" if factory_generated_ids else "PASS",
            "value": {
                "factory_generated_component_count": len(factory_generated_ids),
                "factory_generated_component_ids": factory_generated_ids[:12],
            },
            "detail": "Generated catalog components are hypothesis discovery recipes, not pre-registered evidence.",
        },
        {
            "gate": "component_count_gate",
            "status": "PASS" if component_count >= 3 else "BLOCK",
            "value": component_count,
            "detail": "Requires at least 3 saved strategy components for a toy diagnostic portfolio.",
        },
        {
            "gate": "component_concentration_gate",
            "status": "BLOCK" if top_share > 0.40 else "PASS",
            "value": round(top_share, 8),
            "detail": "Blocks when the best component explains more than 40% of positive portfolio contribution.",
        },
        {
            "gate": "strategy_family_concentration_gate",
            "status": "WARN" if max_family_weight > 0.60 else "PASS",
            "value": round(max_family_weight, 8),
            "detail": "Warns when one sleeve dominates capital allocation.",
        },
        {
            "gate": "correlation_gate",
            "status": "WARN" if avg_abs_corr > 0.75 else "PASS",
            "value": round(avg_abs_corr, 8),
            "detail": "High correlation means components may be the same hidden bet.",
        },
        {
            "gate": "drawdown_gate",
            "status": "WARN" if float(drawdown.min() if not drawdown.empty else 0.0) < -0.25 else "PASS",
            "value": round(float(drawdown.min() if not drawdown.empty else 0.0), 8),
            "detail": "Reports the worst local drawdown of the composed portfolio.",
        },
        {
            "gate": "ex_best_component_gate",
            "status": "BLOCK" if float(returns.sum() if not returns.empty else 0.0) > 0 and ex_best_return <= 0 else "PASS",
            "value": {"best_component": best_component, "ex_best_net_return": round(ex_best_return, 8)},
            "detail": "Replays the portfolio after removing its best component.",
        },
        {
            "gate": "cost_stress_gate",
            "status": "BLOCK" if float(returns.sum() if not returns.empty else 0.0) > 0 and stressed_net <= 0 else "PASS",
            "value": {"stressed_net_return": round(stressed_net, 8), "extra_cost_drag_per_period": round(declared_cost_drag * 0.5, 8)},
            "detail": "Replays the portfolio with 1.5x declared component costs.",
        },
    ]


def _ex_best_return(matrix: pd.DataFrame, allocation: list[dict[str, Any]], best_component: str) -> float:
    remaining = [row for row in allocation if row["component_id"] != best_component]
    if not remaining or matrix.empty:
        return 0.0
    total_weight = sum(float(row["weight"]) for row in remaining) or 1.0
    weights = pd.Series({row["component_id"]: float(row["weight"]) / total_weight for row in remaining})
    return float(matrix.reindex(columns=weights.index, fill_value=0.0).mul(weights, axis=1).sum(axis=1).sum())


def _average_abs_correlation(correlation: pd.DataFrame) -> float:
    if correlation.empty or len(correlation) < 2:
        return 0.0
    values = []
    for row_index in range(len(correlation)):
        for column_index in range(row_index + 1, len(correlation.columns)):
            values.append(abs(float(correlation.iloc[row_index, column_index])))
    return sum(values) / len(values) if values else 0.0


def _high_correlation_pairs(correlation: pd.DataFrame, allocation: list[dict[str, Any]], *, threshold: float = 0.75) -> list[dict[str, Any]]:
    if correlation.empty or len(correlation) < 2:
        return []
    names = {row["component_id"]: _allocation_display_label(row) for row in allocation}
    pairs: list[dict[str, Any]] = []
    for row_index, left in enumerate(correlation.index):
        for column_index, right in enumerate(correlation.columns):
            if column_index <= row_index:
                continue
            value = float(correlation.loc[left, right])
            if abs(value) >= threshold:
                pairs.append(
                    {
                        "left_component_id": str(left),
                        "right_component_id": str(right),
                        "left_strategy": names.get(str(left), str(left)),
                        "right_strategy": names.get(str(right), str(right)),
                        "correlation": round(value, 8),
                    }
                )
    return sorted(pairs, key=lambda row: abs(float(row["correlation"])), reverse=True)


def _build_strategy_deduplication(
    components: list[dict[str, Any]],
    allocation: list[dict[str, Any]],
    correlation: pd.DataFrame,
    contribution: pd.Series,
) -> dict[str, Any]:
    component_by_id = {str(component["component_id"]): component for component in components}
    allocation_ids = [str(row["component_id"]) for row in allocation]
    parent = {component_id: component_id for component_id in allocation_ids}

    def find(component_id: str) -> str:
        while parent[component_id] != component_id:
            parent[component_id] = parent[parent[component_id]]
            component_id = parent[component_id]
        return component_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    reasons: dict[frozenset[str], str] = {}
    for left, right in itertools.combinations(allocation_ids, 2):
        left_component = component_by_id.get(left, {})
        right_component = component_by_id.get(right, {})
        same_template = str(left_component.get("template", "")).lower() == str(right_component.get("template", "")).lower()
        same_mode = str(left_component.get("analysis_mode", "")).lower() == str(right_component.get("analysis_mode", "")).lower()
        same_generated_recipe = (
            _generated_recipe_key(left_component) != ""
            and _generated_recipe_key(left_component) == _generated_recipe_key(right_component)
        )
        corr_value = float(correlation.loc[left, right]) if not correlation.empty and left in correlation.index and right in correlation.columns else 0.0
        if same_generated_recipe:
            union(left, right)
            reasons[frozenset({left, right})] = "same_generated_strategy_recipe"
        elif same_template and same_mode and abs(corr_value) >= 0.98:
            union(left, right)
            reasons[frozenset({left, right})] = "same_template_and_near_identical_returns"

    grouped: dict[str, list[str]] = {}
    for component_id in allocation_ids:
        grouped.setdefault(find(component_id), []).append(component_id)

    groups: list[dict[str, Any]] = []
    deduped: list[str] = []
    removed_count = 0
    allocation_by_id = {str(row["component_id"]): row for row in allocation}
    for ids in grouped.values():
        if len(ids) == 1:
            deduped.append(ids[0])
            continue
        ranked = sorted(
            ids,
            key=lambda component_id: _component_quality_score(component_id, component_by_id, allocation_by_id, contribution),
            reverse=True,
        )
        kept = ranked[0]
        removed = ranked[1:]
        deduped.append(kept)
        removed_count += len(removed)
        reason = next((value for key, value in reasons.items() if len(key.intersection(ids)) == 2), "near_duplicate_strategy_family")
        groups.append(
            {
                "reason": reason,
                "kept_component_id": kept,
                "kept_label": _component_display_label(kept, component_by_id),
                "removed_component_ids": removed,
                "removed_labels": [_component_display_label(component_id, component_by_id) for component_id in removed],
                "group_size": len(ids),
            }
        )
    return {
        "duplicate_group_count": len(groups),
        "removed_component_count": removed_count,
        "deduped_component_ids": [component_id for component_id in allocation_ids if component_id in set(deduped)],
        "groups": groups,
        "rule": "same generated recipe OR same template + same analysis mode + absolute return correlation >= 0.98",
    }


def _generated_recipe_key(component: dict[str, Any]) -> str:
    source = str(component.get("source", "saved_workbench"))
    warnings = {str(warning) for warning in component.get("bias_warnings", [])}
    name = str(component.get("strategy_name", ""))
    generated = source == "factory_generated" or "FACTORY_GENERATED_NOT_PREREGISTERED" in warnings or "Factory " in name
    if not generated:
        return ""
    normalized_name = re.sub(r"^Materialized\s+", "", name, flags=re.IGNORECASE).strip().lower()
    normalized_name = re.sub(r"\s+", " ", normalized_name)
    template = str(component.get("template", "")).strip().lower()
    mode = str(component.get("analysis_mode", "")).strip().lower()
    cost = str(component.get("cost_bps", "")).strip()
    return "|".join([normalized_name, template, mode, cost])


def _build_portfolio_search(
    components: list[dict[str, Any]],
    matrix: pd.DataFrame,
    strategy_deduplication: dict[str, Any],
    *,
    policy: str,
    max_component_weight: float,
    max_rejected_weight: float,
    max_convex_weight: float,
    max_pool_size: int = 12,
    max_subset_size: int = 7,
    max_candidates: int = 5000,
) -> dict[str, Any]:
    component_by_id = {str(component["component_id"]): component for component in components}
    deduped_ids = [component_id for component_id in strategy_deduplication.get("deduped_component_ids", []) if component_id in matrix.columns]
    if len(deduped_ids) < 3:
        return {
            "search_performed": False,
            "optimization_allowed": False,
            "selection_rule": "predeclared_robust_score_no_promotion",
            "reason": "fewer_than_three_deduped_components",
            "best_basket_component_ids": [],
            "best_summary": {},
            "evaluated_candidate_count": 0,
            "overfit_controls": _portfolio_search_controls(max_pool_size, max_subset_size, max_candidates),
        }
    ranking = sorted(deduped_ids, key=lambda component_id: _search_component_rank(component_by_id[component_id], matrix[component_id]), reverse=True)
    pool = ranking[:max_pool_size]
    excluded = ranking[max_pool_size:]
    evaluations: list[dict[str, Any]] = []
    stop = False
    for size in range(3, min(max_subset_size, len(pool)) + 1):
        for ids in itertools.combinations(pool, size):
            evaluations.append(_evaluate_search_basket(list(ids), component_by_id, matrix, policy, max_component_weight, max_rejected_weight, max_convex_weight))
            if len(evaluations) >= max_candidates:
                stop = True
                break
        if stop:
            break
    best = max(evaluations, key=lambda row: row["robust_score"]) if evaluations else {}
    return {
        "search_performed": bool(evaluations),
        "optimization_allowed": False,
        "selection_rule": "predeclared_robust_score_no_promotion",
        "objective": "maximize validation-weighted robust score after duplicate removal, cost stress, contribution concentration, and correlation penalties",
        "search_pool_component_ids": pool,
        "excluded_component_ids": excluded,
        "evaluated_candidate_count": len(evaluations),
        "truncated": stop,
        "exhaustive_within_search_pool": not stop,
        "best_basket_component_ids": best.get("component_ids", []),
        "best_component_labels": [_component_display_label(component_id, component_by_id) for component_id in best.get("component_ids", [])],
        "best_summary": best.get("summary", {}),
        "top_candidates": evaluations[:0] if not evaluations else sorted(evaluations, key=lambda row: row["robust_score"], reverse=True)[:5],
        "overfit_controls": _portfolio_search_controls(max_pool_size, max_subset_size, max_candidates),
        "promotion_allowed": False,
    }


def _portfolio_search_controls(max_pool_size: int, max_subset_size: int, max_candidates: int) -> dict[str, Any]:
    return {
        "diagnostic_only": True,
        "no_provider_query": True,
        "no_market_data_download": True,
        "promotion_locked_false": True,
        "dedupe_before_search": True,
        "max_search_pool_size": max_pool_size,
        "max_subset_size": max_subset_size,
        "max_candidates": max_candidates,
        "why_not_full_optimization": "A fully flexible optimizer would overfit saved dry-run artifacts and manufacture fake edge.",
    }


def _search_component_rank(component: dict[str, Any], series: pd.Series) -> tuple[float, float, float, float]:
    decision = str(component.get("decision", ""))
    decision_score = 0.0 if decision.startswith("REJECTED") or "ARCHIVE" in decision else 1.0
    return (decision_score, float(series.sum()), -float(series.std(ddof=0) or 0.0), float(component.get("trade_count", 0) or 0))


def _evaluate_search_basket(
    component_ids: list[str],
    component_by_id: dict[str, dict[str, Any]],
    matrix: pd.DataFrame,
    policy: str,
    max_component_weight: float,
    max_rejected_weight: float,
    max_convex_weight: float,
) -> dict[str, Any]:
    subset_components = [component_by_id[component_id] for component_id in component_ids]
    subset_matrix = matrix.reindex(columns=component_ids, fill_value=0.0)
    allocation = build_portfolio_allocation(
        subset_components,
        subset_matrix,
        policy=policy,
        max_component_weight=max_component_weight,
        max_rejected_weight=max_rejected_weight,
        max_convex_weight=max_convex_weight,
    )
    weights = pd.Series({row["component_id"]: row["weight"] for row in allocation}, dtype=float)
    weighted = subset_matrix.reindex(columns=weights.index, fill_value=0.0).mul(weights, axis=1)
    returns = weighted.sum(axis=1)
    cumulative = returns.cumsum()
    drawdown = cumulative - cumulative.cummax()
    contribution = weighted.sum(axis=0).sort_values(ascending=False)
    positive_total = float(contribution[contribution > 0].sum()) if not contribution.empty else 0.0
    top_share = float(contribution.iloc[0] / positive_total) if positive_total > 0 and not contribution.empty else 0.0
    corr = subset_matrix.reindex(columns=weights.index).corr().fillna(0.0) if len(weights) > 1 else pd.DataFrame()
    avg_corr = _average_abs_correlation(corr)
    ex_best = _ex_best_return(subset_matrix, allocation, str(contribution.index[0]) if not contribution.empty else "")
    declared_cost_drag = _weighted_cost_drag(subset_components, allocation)
    stressed_total = float(returns.sum() - declared_cost_drag * max(1, len(returns)) * 0.5)
    split = max(1, len(returns) // 2)
    train_total = float(returns.iloc[:split].sum())
    validation_total = float(returns.iloc[split:].sum())
    robust_score = (
        validation_total
        + 0.25 * train_total
        + 0.25 * ex_best
        + 0.25 * stressed_total
        - max(0.0, top_share - 0.35)
        - max(0.0, avg_corr - 0.65)
        + float(drawdown.min() if not drawdown.empty else 0.0)
    )
    return {
        "component_ids": component_ids,
        "robust_score": round(float(robust_score), 8),
        "summary": {
            "component_count": len(component_ids),
            "total_net_return": round(float(returns.sum()), 8),
            "train_net_return": round(train_total, 8),
            "validation_net_return": round(validation_total, 8),
            "stressed_net_return": round(stressed_total, 8),
            "ex_best_net_return": round(ex_best, 8),
            "top_component_contribution": round(top_share, 8),
            "average_abs_correlation": round(avg_corr, 8),
            "max_drawdown": round(float(drawdown.min() if not drawdown.empty else 0.0), 8),
        },
    }


def _build_auto_clean_plan(
    components: list[dict[str, Any]],
    allocation: list[dict[str, Any]],
    contribution: pd.Series,
    high_correlation_pairs: list[dict[str, Any]],
    *,
    min_components: int = 3,
) -> dict[str, Any]:
    kept = {str(row["component_id"]) for row in allocation}
    component_by_id = {str(component["component_id"]): component for component in components}
    allocation_by_id = {str(row["component_id"]): row for row in allocation}
    removed: list[dict[str, Any]] = []
    for pair in high_correlation_pairs:
        left = str(pair["left_component_id"])
        right = str(pair["right_component_id"])
        if left not in kept or right not in kept:
            continue
        if len(kept) <= min_components:
            break
        remove_id = _choose_component_to_remove(left, right, component_by_id, allocation_by_id, contribution)
        keep_id = right if remove_id == left else left
        kept.remove(remove_id)
        removed.append(
            {
                "component_id": remove_id,
                "strategy_name": component_by_id.get(remove_id, {}).get("strategy_name", remove_id),
                "component_label": _component_display_label(remove_id, component_by_id),
                "paired_with_component_id": keep_id,
                "paired_with_strategy": component_by_id.get(keep_id, {}).get("strategy_name", keep_id),
                "paired_with_label": _component_display_label(keep_id, component_by_id),
                "correlation": pair["correlation"],
                "reason": _auto_clean_reason(remove_id, keep_id, component_by_id, contribution),
            }
        )
    return {
        "available": bool(removed),
        "threshold": 0.75,
        "min_components": min_components,
        "kept_component_ids": [row["component_id"] for row in allocation if row["component_id"] in kept],
        "removed_components": removed,
        "summary": _auto_clean_summary(removed),
    }


def _choose_component_to_remove(
    left: str,
    right: str,
    component_by_id: dict[str, dict[str, Any]],
    allocation_by_id: dict[str, dict[str, Any]],
    contribution: pd.Series,
) -> str:
    left_score = _component_quality_score(left, component_by_id, allocation_by_id, contribution)
    right_score = _component_quality_score(right, component_by_id, allocation_by_id, contribution)
    return left if left_score < right_score else right


def _component_display_label(component_id: str, component_by_id: dict[str, dict[str, Any]]) -> str:
    component = component_by_id.get(component_id, {})
    name = str(component.get("strategy_name") or component_id)
    template = str(component.get("template") or "custom")
    short_id = _short_component_id(component_id)
    return f"{name} ({template}, {short_id})"


def _allocation_display_label(row: dict[str, Any]) -> str:
    component_id = str(row.get("component_id", ""))
    name = str(row.get("strategy_name") or component_id)
    template = str(row.get("template") or "custom")
    return f"{name} ({template}, {_short_component_id(component_id)})"


def _short_component_id(component_id: str) -> str:
    if component_id.startswith("FACTORY-"):
        return f"F-{component_id.removeprefix('FACTORY-')[:6]}"
    return component_id[:6]


def _component_quality_score(
    component_id: str,
    component_by_id: dict[str, dict[str, Any]],
    allocation_by_id: dict[str, dict[str, Any]],
    contribution: pd.Series,
) -> tuple[float, float, float, float]:
    component = component_by_id.get(component_id, {})
    decision = str(component.get("decision", ""))
    decision_score = 0.0 if decision.startswith("REJECTED") or "ARCHIVE" in decision else 1.0
    contribution_score = float(contribution.get(component_id, 0.0)) if not contribution.empty else 0.0
    trade_count_score = float(component.get("trade_count", 0) or 0)
    warning_penalty = -float(len(component.get("bias_warnings", [])))
    sleeve_score = 0.1 if allocation_by_id.get(component_id, {}).get("sleeve") == "core" else 0.0
    return (decision_score, contribution_score + sleeve_score, trade_count_score, warning_penalty)


def _auto_clean_reason(
    remove_id: str,
    keep_id: str,
    component_by_id: dict[str, dict[str, Any]],
    contribution: pd.Series,
) -> str:
    removed = component_by_id.get(remove_id, {})
    kept = component_by_id.get(keep_id, {})
    removed_contribution = float(contribution.get(remove_id, 0.0)) if not contribution.empty else 0.0
    kept_contribution = float(contribution.get(keep_id, 0.0)) if not contribution.empty else 0.0
    if str(removed.get("decision", "")).startswith("REJECTED") and not str(kept.get("decision", "")).startswith("REJECTED"):
        return "Removed the rejected component in a highly correlated pair."
    if removed_contribution <= kept_contribution:
        return "Removed the lower-contribution component in a highly correlated pair."
    return "Removed the less robust duplicate to preserve component diversity."


def _auto_clean_summary(removed: list[dict[str, Any]]) -> str:
    if not removed:
        return "No automatic de-duplication suggested."
    first = removed[0]
    return (
        f"Remove {len(removed)} duplicated component(s). Start with "
        f"{first.get('component_label', first['strategy_name'])} because it overlaps with "
        f"{first.get('paired_with_label', first['paired_with_strategy'])}."
    )


def _build_action_plan(
    gate_panel: list[dict[str, Any]],
    allocation: list[dict[str, Any]],
    contribution: pd.Series,
    high_correlation_pairs: list[dict[str, Any]],
    final_decision: dict[str, Any],
) -> list[dict[str, str]]:
    gates = {row["gate"]: row for row in gate_panel}
    allocation_by_id = {str(row["component_id"]): row for row in allocation}

    def allocation_label(component_id: str) -> str:
        row = allocation_by_id.get(component_id, {})
        return _allocation_display_label(row) if row else component_id

    actions: list[dict[str, str]] = []
    if final_decision["blockers"]:
        actions.append(
            {
                "severity": "block",
                "title": _human_decision_title(str(final_decision["decision"])),
                "action": _human_decision_action(str(final_decision["decision"])),
            }
        )
    if high_correlation_pairs:
        first = high_correlation_pairs[0]
        left = str(first["left_component_id"])
        right = str(first["right_component_id"])
        actions.append(
            {
                "severity": "warn",
                "title": f"{len(high_correlation_pairs)} highly correlated component pair(s)",
                "action": f"Start by removing either {allocation_label(left)} or {allocation_label(right)}, then rerun. They appear to be overlapping bets.",
            }
        )
    concentration = gates.get("component_concentration_gate", {})
    if concentration.get("status") == "BLOCK" and not contribution.empty:
        best_id = str(contribution.index[0])
        actions.append(
            {
                "severity": "block",
                "title": "One component dominates the portfolio",
                "action": f"Remove or cap {allocation_label(best_id)}, then add at least two components from different sleeves before rerunning.",
            }
        )
    cost_stress = gates.get("cost_stress_gate", {})
    if cost_stress.get("status") == "BLOCK" and final_decision["decision"] != "PORTFOLIO_ARCHIVE_COST_STRESS_FAILED":
        actions.append(
            {
                "severity": "block",
                "title": "The basket fails under tougher costs",
                "action": "Try longer-horizon components, lower-turnover rules, or maker-style execution assumptions. Do not treat the current basket as robust.",
            }
        )
    data_gate = gates.get("data_contract_gate", {})
    if data_gate.get("status") == "WARN":
        actions.append(
            {
                "severity": "warn",
                "title": "Data quality keeps this diagnostic-only",
                "action": "Resolve PIT, delisted, or proxy-data warnings before interpreting this as real strategy evidence.",
            }
        )
    if not actions:
        actions.append(
            {
                "severity": "pass",
                "title": "No immediate structural action",
                "action": "The local portfolio passed current gates, but promotion is still forbidden until a real governed backtest exists.",
            }
        )
    return actions


def _human_decision_title(decision: str) -> str:
    return {
        "PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY": "Factory search is diagnostic-only",
        "PORTFOLIO_ARCHIVE_CONCENTRATION_FAILED": "Failed because return is too concentrated",
        "PORTFOLIO_ARCHIVE_COST_STRESS_FAILED": "Failed because costs erase the basket",
        "PORTFOLIO_ARCHIVE_INSUFFICIENT_COMPONENTS": "Failed because there are too few components",
        "PORTFOLIO_ARCHIVE_EX_BEST_COMPONENT_FAILED": "Failed because the best component carries the portfolio",
        "PORTFOLIO_ARCHIVE_DATA_CONTRACT_FAILED": "Failed because the data contract is not strong enough",
    }.get(decision, decision.replace("_", " ").title())


def _human_decision_action(decision: str) -> str:
    return {
        "PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY": "Convert the generated components into explicit Workbench manifests, pre-register them, and rerun before reading candidate status.",
        "PORTFOLIO_ARCHIVE_CONCENTRATION_FAILED": "Reduce the top contributor weight or add genuinely different components before rerunning.",
        "PORTFOLIO_ARCHIVE_COST_STRESS_FAILED": "Lower turnover, use longer holding periods, or test execution assumptions before trusting the result.",
        "PORTFOLIO_ARCHIVE_INSUFFICIENT_COMPONENTS": "Add at least three saved strategy components before reading portfolio-level metrics.",
        "PORTFOLIO_ARCHIVE_EX_BEST_COMPONENT_FAILED": "Remove the best component and rebuild the basket; if the sign flips, the portfolio is not diversified.",
        "PORTFOLIO_ARCHIVE_DATA_CONTRACT_FAILED": "Fix data-quality blockers before using this as evidence.",
    }.get(decision, "Inspect the blocking gates and rerun after changing one thing at a time.")


def _weighted_cost_drag(components: list[dict[str, Any]], allocation: list[dict[str, Any]]) -> float:
    cost_by_id = {str(component["component_id"]): float(component.get("cost_bps", 0)) / 10000.0 for component in components}
    return sum(float(row["weight"]) * cost_by_id.get(row["component_id"], 0.0) for row in allocation)


def _build_final_decision(gate_panel: list[dict[str, Any]], returns: pd.Series, components: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [row["gate"] for row in gate_panel if row["status"] == "BLOCK"]
    decision = "PORTFOLIO_DIAGNOSTIC_COMPLETE_NO_PROMOTION"
    if "factory_generated_scope_gate" in blockers:
        decision = "PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY"
    elif "component_count_gate" in blockers:
        decision = "PORTFOLIO_ARCHIVE_INSUFFICIENT_COMPONENTS"
    elif "ex_best_component_gate" in blockers:
        decision = "PORTFOLIO_ARCHIVE_EX_BEST_COMPONENT_FAILED"
    elif "cost_stress_gate" in blockers:
        decision = "PORTFOLIO_ARCHIVE_COST_STRESS_FAILED"
    elif "component_concentration_gate" in blockers:
        decision = "PORTFOLIO_ARCHIVE_CONCENTRATION_FAILED"
    elif not blockers and float(returns.sum() if not returns.empty else 0.0) > 0 and len(components) >= 5:
        decision = "PORTFOLIO_RESEARCH_BASKET_CANDIDATE_ONLY"
    return {
        "decision": decision,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "portfolio_backtest_performed": False,
        "runner_mode": "diagnostic_local_portfolio_composer",
        "blockers": blockers,
        "net_return_sum": round(float(returns.sum() if not returns.empty else 0.0), 8),
    }


def _portfolio_signature(
    components: list[dict[str, Any]],
    policy: str,
    max_component_weight: float,
    max_rejected_weight: float,
    max_convex_weight: float,
) -> str:
    payload = {
        "components": [component.get("component_id") for component in components],
        "policy": policy,
        "max_component_weight": max_component_weight,
        "max_rejected_weight": max_rejected_weight,
        "max_convex_weight": max_convex_weight,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def persist_portfolio_diagnostic(diagnostic: dict[str, Any], *, root: Path = Path(".")) -> dict[str, str]:
    signature = str(diagnostic["summary"]["portfolio_signature"])
    output_dir = Path(root) / PORTFOLIO_OUTPUT_DIR / signature
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "output_dir": output_dir,
        "portfolio_manifest_path": output_dir / "portfolio_manifest.json",
        "component_manifest_path": output_dir / "component_manifest.csv",
        "component_return_matrix_path": output_dir / "component_return_matrix.csv",
        "allocation_table_path": output_dir / "allocation_table.csv",
        "portfolio_equity_curve_path": output_dir / "portfolio_equity_curve.csv",
        "portfolio_drawdown_path": output_dir / "portfolio_drawdown.csv",
        "portfolio_correlation_matrix_path": output_dir / "portfolio_correlation_matrix.csv",
        "portfolio_high_correlation_pairs_path": output_dir / "portfolio_high_correlation_pairs.csv",
        "portfolio_auto_clean_plan_path": output_dir / "portfolio_auto_clean_plan.json",
        "portfolio_deduplication_path": output_dir / "portfolio_deduplication.json",
        "portfolio_search_path": output_dir / "portfolio_search.json",
        "portfolio_gate_panel_path": output_dir / "portfolio_gate_panel.json",
        "portfolio_action_plan_path": output_dir / "portfolio_action_plan.json",
        "portfolio_final_decision_path": output_dir / "portfolio_final_decision.json",
        "portfolio_vault_report_path": output_dir / "portfolio_vault_report.md",
    }
    _write_json(paths["portfolio_manifest_path"], diagnostic["portfolio_manifest"])
    pd.DataFrame(diagnostic["components"]).to_csv(paths["component_manifest_path"], index=False)
    pd.DataFrame(diagnostic["return_matrix"]).to_csv(paths["component_return_matrix_path"], index=False)
    pd.DataFrame(diagnostic["allocation"]).to_csv(paths["allocation_table_path"], index=False)
    pd.DataFrame(diagnostic["equity_curve"]).to_csv(paths["portfolio_equity_curve_path"], index=False)
    pd.DataFrame(diagnostic["drawdown"]).to_csv(paths["portfolio_drawdown_path"], index=False)
    pd.DataFrame(diagnostic["correlation_matrix"]).to_csv(paths["portfolio_correlation_matrix_path"], index=False)
    pd.DataFrame(diagnostic["high_correlation_pairs"]).to_csv(paths["portfolio_high_correlation_pairs_path"], index=False)
    _write_json(paths["portfolio_auto_clean_plan_path"], diagnostic["auto_clean"])
    _write_json(paths["portfolio_deduplication_path"], diagnostic["strategy_deduplication"])
    _write_json(paths["portfolio_search_path"], diagnostic["portfolio_search"])
    _write_json(paths["portfolio_gate_panel_path"], diagnostic["gate_panel"])
    _write_json(paths["portfolio_action_plan_path"], diagnostic["action_plan"])
    _write_json(paths["portfolio_final_decision_path"], diagnostic["final_decision"])
    paths["portfolio_vault_report_path"].write_text(_portfolio_report(diagnostic), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _portfolio_report(diagnostic: dict[str, Any]) -> str:
    summary = diagnostic["summary"]
    final = diagnostic["final_decision"]
    lines = [
        "# WORKBENCH-PORTFOLIO-001 Diagnostic Report",
        "",
        "## Verdict",
        "",
        f"- decision: `{final['decision']}`",
        f"- promotion_allowed: `{final['promotion_allowed']}`",
        f"- provider_query_performed: `{final['provider_query_performed']}`",
        f"- net_return_sum: `{final['net_return_sum']}`",
        "",
        "## Portfolio",
        "",
        f"- component_count: `{summary['component_count']}`",
        f"- policy: `{summary['policy']}`",
        f"- total_net_return: `{summary['total_net_return']}`",
        f"- max_drawdown: `{summary['max_drawdown']}`",
        f"- max_drawdown_pct_context: `{summary['max_drawdown_pct']}`",
        f"- time_underwater_ratio: `{summary['time_underwater_ratio']}`",
        "",
        "## Auto-Clean Basket",
        "",
        f"- available: `{diagnostic.get('auto_clean', {}).get('available', False)}`",
        f"- summary: {diagnostic.get('auto_clean', {}).get('summary', 'No automatic de-duplication suggested.')}",
        "",
        "## Governed Search",
        "",
        f"- duplicate_groups: `{diagnostic.get('strategy_deduplication', {}).get('duplicate_group_count', 0)}`",
        f"- duplicates_removed: `{diagnostic.get('strategy_deduplication', {}).get('removed_component_count', 0)}`",
        f"- candidates_evaluated: `{diagnostic.get('portfolio_search', {}).get('evaluated_candidate_count', 0)}`",
        f"- best_basket: `{diagnostic.get('portfolio_search', {}).get('best_basket_component_ids', [])}`",
        f"- promotion_allowed: `{diagnostic.get('portfolio_search', {}).get('promotion_allowed', False)}`",
        "",
        "## Recommended Actions",
        "",
        *[f"- `{row['severity']}` {row['title']}: {row['action']}" for row in diagnostic.get("action_plan", [])],
        "",
        "## Governance",
        "",
        "This diagnostic composes saved local Workbench artifacts only. It cannot query providers, download market data, paper trade, live trade, or promote a portfolio.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--policy", default="sleeve_allocation", choices=["equal_weight", "inverse_volatility", "sleeve_allocation"])
    parser.add_argument("--paper", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--provider-query", action="store_true")
    parser.add_argument("--download-market-data", action="store_true")
    args = parser.parse_args(argv)
    if args.paper or args.live or args.promote or args.provider_query or args.download_market_data:
        print(json.dumps({"error": "forbidden_flag_present"}, indent=2, sort_keys=True))
        return 2
    components = load_workbench_portfolio_components(root=args.root)
    diagnostic = run_portfolio_diagnostic(components, policy=args.policy)
    paths = persist_portfolio_diagnostic(diagnostic, root=args.root)
    print(json.dumps(paths, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
