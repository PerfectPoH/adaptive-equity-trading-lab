from __future__ import annotations

import pandas as pd

from src.analysis.threshold_analyzer import build_threshold_diagnostics


def test_threshold_diagnostics_recommends_validation_threshold() -> None:
    idx = pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04", "2024-01-02"])
    signals = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "AAA", "AAA"],
            "scanner_score": [80, 80, 80, 80],
            "model_probability": [0.41, 0.56, 0.66, 0.56],
            "spy_trend_positive": [True, True, True, True],
            "execution_valid": [True, True, True, True],
            "label": [0, 1, 1, 1],
        },
        index=idx,
    )

    diagnostics, summary = build_threshold_diagnostics(signals, thresholds=[0.40, 0.55, 0.65])

    assert set(diagnostics["period"]) == {"validation", "test"}
    assert summary["recommended_threshold"] == 0.55
    assert summary["validation_success_rate"] == 1.0
