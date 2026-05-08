from __future__ import annotations

import pandas as pd

from src.analysis.calibration import summarize_calibration


def test_summarize_calibration_uses_weighted_abs_error() -> None:
    calibration = pd.DataFrame(
        [
            {"period": "test", "count": 10, "abs_error": 0.1, "brier_score": 0.2},
            {"period": "test", "count": 30, "abs_error": 0.3, "brier_score": 0.2},
        ]
    )

    summary = summarize_calibration(calibration)

    assert summary["test"]["rows"] == 40
    assert round(summary["test"]["mean_abs_calibration_error"], 4) == 0.25
    assert summary["test"]["max_abs_calibration_error"] == 0.3
