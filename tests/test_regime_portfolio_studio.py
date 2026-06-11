from __future__ import annotations

import pandas as pd

from src.experiments.regime_portfolio_studio import (
    component_strategy_family,
    compose_regime_switching_portfolio,
    optimize_basket_for_regime,
    regime_allowed_components,
    run_regime_studio,
)


def _component(idx: int, name: str, drift: float, periods: int = 80) -> dict:
    rows = [
        {
            "period": str(pd.Timestamp("2024-01-01") + pd.Timedelta(days=k)),
            "net_return": drift + 0.002 * ((k * (idx + 2)) % 7 - 3),
        }
        for k in range(periods)
    ]
    return {
        "component_id": f"C{idx}",
        "strategy_name": name,
        "template": name,
        "analysis_mode": "local",
        "decision": "DIAGNOSTIC",
        "promotion_allowed": False,
        "bias_warnings": [],
        "source": "saved_workbench",
        "trade_count": periods,
        "net_return_sum": sum(r["net_return"] for r in rows),
        "cost_drag": 0.0,
        "inline_returns": rows,
    }


def _router() -> pd.DataFrame:
    rows = []
    for family in ["Momentum", "Mean Reversion", "Event Catalyst", "Regime Risk Engine", "Dollar-Bar Microstructure", "9:30 AM ORB"]:
        rows.append({"regime_label": "TREND_UP_LOW_VOL", "strategy_family": family, "posture": "ALLOW_PROXY", "why": ""})
        rows.append(
            {
                "regime_label": "DRAWDOWN_STRESS",
                "strategy_family": family,
                "posture": "BLOCK" if family == "Momentum" else "REDUCE",
                "why": "",
            }
        )
    return pd.DataFrame(rows)


def _components() -> list[dict]:
    return [
        _component(0, "Momentum breakout", 0.002),
        _component(1, "Momentum xmom", 0.001),
        _component(2, "GapRev mean reversion", 0.0015),
        _component(3, "LowVol reversion", 0.0005),
        _component(4, "Regime risk engine", 0.0008),
        _component(5, "Event catalyst pead", -0.0005),
    ]


def _regime_map() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=80)
    labels = ["TREND_UP_LOW_VOL"] * 40 + ["DRAWDOWN_STRESS"] * 40
    return pd.DataFrame({"date": dates, "regime_label": labels})


def test_family_classifier_matches_expected_families() -> None:
    assert component_strategy_family({"template": "Momentum xmom", "strategy_name": ""}) == "Momentum"
    assert component_strategy_family({"template": "", "strategy_name": "GapRev daily"}) == "Mean Reversion"
    assert component_strategy_family({"template": "Regime filter", "strategy_name": ""}) == "Regime Risk Engine"


def test_blocked_families_are_excluded_per_regime() -> None:
    allowed, blocked = regime_allowed_components(_components(), _router(), "DRAWDOWN_STRESS")
    families_allowed = {component["regime_family"] for component in allowed}
    assert "Momentum" not in families_allowed
    assert any(component["regime_family"] == "Momentum" for component in blocked)


def test_optimize_basket_returns_weights_and_diagnostic_summary() -> None:
    basket = optimize_basket_for_regime(_components(), _router(), "TREND_UP_LOW_VOL")
    assert basket["status"] == "BASKET_SELECTED_DIAGNOSTIC_ONLY"
    assert basket["promotion_allowed"] is False
    assert basket["basket_component_ids"]
    assert abs(sum(basket["weights"].values()) - 1.0) < 1e-6


def test_composition_is_finite_and_mode_aware() -> None:
    components = _components()
    router = _router()
    baskets = {
        regime: optimize_basket_for_regime(components, router, regime)
        for regime in ["TREND_UP_LOW_VOL", "DRAWDOWN_STRESS"]
    }
    result = compose_regime_switching_portfolio(components, baskets, _regime_map())
    summary = result["summary"]
    assert summary["aggregation_mode"] in {"compounded", "additive"}
    for key in ("dynamic_total", "static_total", "dynamic_max_drawdown"):
        assert abs(float(summary[key])) < 1e6, f"{key} esploso: {summary[key]}"
    curves = result["curves"]
    assert {"period", "regime", "dynamic", "static"}.issubset(curves.columns)
    assert (curves["regime"].iloc[:5] == "TREND_UP_LOW_VOL").all()


def test_full_pipeline_emits_baskets_for_every_router_regime() -> None:
    result = run_regime_studio(_components(), _router(), _regime_map())
    assert result["promotion_allowed"] is False
    assert set(result["baskets_by_regime"]) == {"TREND_UP_LOW_VOL", "DRAWDOWN_STRESS"}
    assert result["composition"]["status"] == "REGIME_STUDIO_DIAGNOSTIC_ONLY"


def test_extreme_streams_fall_back_to_additive_mode() -> None:
    components = _components()
    wild = _component(9, "Momentum wild", 0.0)
    for row in wild["inline_returns"]:
        row["net_return"] = 4.0  # +400% per periodo: non frazionario
    components.append(wild)
    router = _router()
    baskets = {r: optimize_basket_for_regime(components, router, r) for r in ["TREND_UP_LOW_VOL", "DRAWDOWN_STRESS"]}
    result = compose_regime_switching_portfolio(components, baskets, _regime_map())
    assert result["summary"]["aggregation_mode"] == "additive"
    assert abs(result["summary"]["dynamic_total"]) < 1e6
