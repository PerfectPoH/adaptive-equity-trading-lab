from __future__ import annotations

import pandas as pd

from src.features.feature_pipeline import build_features
from src.models.trainer import temporal_split
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


def test_temporal_split_purges_rows_whose_labels_cross_boundaries() -> None:
    idx = pd.bdate_range("2022-12-01", periods=55)
    rows = []
    for symbol in ("AAA", "BBB"):
        frame = pd.DataFrame(
            {
                "symbol": symbol,
                "feature": range(len(idx)),
                "label": 1,
                "label_executable": True,
            },
            index=idx,
        )
        rows.append(frame)
    data = pd.concat(rows).sort_index()

    split = temporal_split(
        data,
        train_end="2022-12-30",
        validation_end="2023-01-31",
        test_end="2023-02-28",
        label_horizon_bars=3,
    )

    raw_train = data.loc[:"2022-12-30"]
    raw_validation = data.loc["2022-12-31":"2023-01-31"]
    for symbol in ("AAA", "BBB"):
        expected_train_last = raw_train[raw_train["symbol"] == symbol].index[-4]
        expected_validation_last = raw_validation[raw_validation["symbol"] == symbol].index[-4]

        assert split.train[split.train["symbol"] == symbol].index.max() == expected_train_last
        assert split.validation[split.validation["symbol"] == symbol].index.max() == expected_validation_last


def test_temporal_split_applies_embargo_after_boundaries() -> None:
    idx = pd.date_range("2023-01-01", periods=10)
    data = pd.DataFrame({"feature": range(len(idx)), "label": 1, "label_executable": True}, index=idx)

    split = temporal_split(
        data,
        train_end="2023-01-03",
        validation_end="2023-01-06",
        test_end="2023-01-10",
        label_horizon_bars=0,
        embargo_days=2,
    )

    assert split.train.index.max() == pd.Timestamp("2023-01-03")
    assert split.validation.index.min() == pd.Timestamp("2023-01-06")
    assert split.test.index.min() == pd.Timestamp("2023-01-09")
