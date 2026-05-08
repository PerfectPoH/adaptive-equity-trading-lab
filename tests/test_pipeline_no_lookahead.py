from __future__ import annotations

import pandas as pd

from src.features.feature_pipeline import build_features
from src.scanner.stock_scanner import add_scanner_columns


def make_frame(rows: int = 120) -> pd.DataFrame:
    idx = pd.bdate_range("2022-01-03", periods=rows)
    close = pd.Series([100 + i * 0.2 for i in range(rows)], index=idx)
    return pd.DataFrame(
        {
            "Open": close - 0.1,
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": [1_000_000 + i * 1_000 for i in range(rows)],
        },
        index=idx,
    )


def test_future_price_mutation_does_not_change_past_scanner_output() -> None:
    frame = make_frame()
    cutoff = frame.index[70]
    mutated = frame.copy()
    mutated.loc[mutated.index > cutoff, "Close"] = mutated.loc[mutated.index > cutoff, "Close"] * 50
    mutated.loc[mutated.index > cutoff, "High"] = mutated.loc[mutated.index > cutoff, "High"] * 50
    mutated.loc[mutated.index > cutoff, "Low"] = mutated.loc[mutated.index > cutoff, "Low"] * 50

    scanned = add_scanner_columns(build_features(frame))
    mutated_scanned = add_scanner_columns(build_features(mutated))

    columns = ["scanner_score", "scanner_pass"]
    pd.testing.assert_frame_equal(scanned.loc[:cutoff, columns], mutated_scanned.loc[:cutoff, columns])
