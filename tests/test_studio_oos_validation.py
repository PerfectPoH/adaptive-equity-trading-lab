from __future__ import annotations

import pandas as pd

from src.experiments.studio_oos_validation import OosConfig, run_studio_oos_validation, truncate_components


def _component(idx: int, name: str, drift: float, periods: int = 400) -> dict:
    rows = [
        {
            "period": str(pd.Timestamp("2023-01-01") + pd.Timedelta(days=k)),
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


def _components() -> list[dict]:
    return [
        _component(0, "Momentum breakout", 0.002),
        _component(1, "Momentum xmom", 0.001),
        _component(2, "GapRev mean reversion", 0.0015),
        _component(3, "LowVol reversion", 0.0005),
        _component(4, "Regime risk engine", 0.0008),
        _component(5, "Event catalyst pead", -0.0005),
    ]


def _router() -> pd.DataFrame:
    rows = []
    for family in ["Momentum", "Mean Reversion", "Event Catalyst", "Regime Risk Engine", "Dollar-Bar Microstructure", "9:30 AM ORB"]:
        rows.append({"regime_label": "TREND_UP_LOW_VOL", "strategy_family": family, "posture": "ALLOW_PROXY", "why": ""})
        rows.append({"regime_label": "DRAWDOWN_STRESS", "strategy_family": family, "posture": "REDUCE", "why": ""})
    return pd.DataFrame(rows)


def _regime_map() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=400)
    labels = ["TREND_UP_LOW_VOL"] * 200 + ["DRAWDOWN_STRESS"] * 200
    return pd.DataFrame({"date": dates, "regime_label": labels})


def test_truncate_removes_post_cutoff_periods() -> None:
    cut = pd.Timestamp("2023-06-01")
    truncated = truncate_components(_components(), cut)
    assert truncated
    for component in truncated:
        last = max(pd.Timestamp(r["period"]) for r in component["inline_returns"])
        assert last < cut


def test_oos_validation_runs_and_uses_only_pre_cutoff_for_selection() -> None:
    result = run_studio_oos_validation(
        _components(), _router(), _regime_map(),
        OosConfig(cutoff="2023-09-01", min_oos_periods=50),
    )
    assert result["status"] == "STUDIO_OOS_VALIDATION_COMPLETE"
    assert result["promotion_allowed"] is False
    assert result["config"]["oos_periods"] >= 50
    s = result["summary"]
    assert abs(float(s["dynamic_total_oos"])) < 1e6
    gate = result["statistical_gate"]
    assert 0.0 <= gate["dsr"] <= 1.0
    assert gate["trial_count"] >= 2
    assert "OOS_" in result["verdict"]


def test_insufficient_oos_periods_blocks() -> None:
    result = run_studio_oos_validation(
        _components(), _router(), _regime_map(),
        OosConfig(cutoff="2024-01-20", min_oos_periods=100),
    )
    assert result["status"] == "INSUFFICIENT_OOS_PERIODS"
