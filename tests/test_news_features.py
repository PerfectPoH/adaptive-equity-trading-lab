from __future__ import annotations

import pandas as pd

from src.features.news_features import add_market_news_features


def test_market_news_features_are_lagged_one_day() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    frame = pd.DataFrame({"Close": [100, 101, 102]}, index=idx)
    news = pd.DataFrame(
        {
            "news_market_article_count": [10, 20, 30],
            "news_market_volume_share": [0.1, 0.2, 0.3],
            "news_market_avg_tone": [-1.0, 2.0, -3.0],
            "news_market_tone_abs": [1.0, 2.0, 3.0],
            "news_market_article_count_3d": [10, 15, 20],
            "news_market_volume_share_3d": [0.1, 0.15, 0.2],
            "news_market_avg_tone_3d": [-1.0, 0.5, -0.67],
            "news_market_stress": [0.1, 0.0, 0.134],
        },
        index=idx,
    )

    featured = add_market_news_features(frame, news)

    assert featured["news_market_article_count"].iloc[0] == 0
    assert featured["news_market_article_count"].iloc[1] == 10
    assert featured["news_market_avg_tone"].iloc[2] == 2.0
