from __future__ import annotations

import pandas as pd


NEWS_FEATURE_COLUMNS = [
    "news_market_article_count",
    "news_market_volume_share",
    "news_market_avg_tone",
    "news_market_tone_abs",
    "news_market_article_count_3d",
    "news_market_volume_share_3d",
    "news_market_avg_tone_3d",
    "news_market_stress",
]


def add_market_news_features(frame: pd.DataFrame, market_news: pd.DataFrame | None = None) -> pd.DataFrame:
    data = frame.copy().sort_index()
    if market_news is None or market_news.empty:
        for column in NEWS_FEATURE_COLUMNS:
            data[column] = 0.0
        data["news_feature_available"] = False
        return data

    news = market_news.copy().sort_index()
    news.index = pd.to_datetime(news.index).normalize()
    news = news.reindex(pd.date_range(news.index.min(), news.index.max(), freq="D")).ffill().fillna(0)

    # Signals are generated after the equity close. Use previous-day news
    # context to avoid accidental future/intraday leakage from UTC news buckets.
    lagged = news.shift(1).fillna(0)
    aligned = lagged.reindex(pd.to_datetime(data.index).normalize()).fillna(0)

    for column in NEWS_FEATURE_COLUMNS:
        data[column] = pd.to_numeric(aligned.get(column, 0), errors="coerce").fillna(0).to_numpy()
    data["news_feature_available"] = (aligned[NEWS_FEATURE_COLUMNS].abs().sum(axis=1) > 0).to_numpy()
    return data
