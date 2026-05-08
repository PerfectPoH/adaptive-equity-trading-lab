from __future__ import annotations

import pandas as pd

from src.analysis.regime_analyzer import build_feature_regime_analysis


def test_build_feature_regime_analysis_finds_loss_regimes() -> None:
    trades = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B", "C", "C"],
            "return_pct": [-0.03, -0.02, 0.04, 0.05, -0.01, 0.03],
            "pnl": [-300, -200, 400, 500, -100, 300],
            "signal_atr_pct": [0.05, 0.06, 0.01, 0.02, 0.05, 0.02],
            "signal_model_probability": [0.7, 0.68, 0.55, 0.56, 0.66, 0.57],
        }
    )

    regimes, contrasts, summary = build_feature_regime_analysis(trades, min_bin_count=1)

    assert not regimes.empty
    assert not contrasts.empty
    assert summary["total_trades"] == 6
    assert summary["losses"] == 3
    assert summary["worst_regimes"]
    assert summary["primary_findings"]


def test_build_feature_regime_analysis_handles_empty_trades() -> None:
    regimes, contrasts, summary = build_feature_regime_analysis(pd.DataFrame())

    assert regimes.empty
    assert contrasts.empty
    assert summary["total_trades"] == 0
