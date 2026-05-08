from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential


GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_MARKET_QUERY = '("stock market" OR "Federal Reserve" OR inflation OR recession OR earnings OR economy)'
CACHE_PATH = Path("data/news/gdelt_market_news_daily.csv")


def load_or_download_market_news(
    start: str,
    end: str,
    query: str = DEFAULT_MARKET_QUERY,
    cache_path: Path = CACHE_PATH,
    pause_seconds: float = 0.6,
) -> pd.DataFrame:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        cached = _read_cached(cache_path)
        if _covers_range(cached, start, end):
            return cached

    try:
        news = download_market_news(start, end, query=query, pause_seconds=pause_seconds)
    except Exception:  # noqa: BLE001 - news is experimental and must not break price pipeline.
        if cache_path.exists():
            return _read_cached(cache_path)
        return neutral_market_news(start, end)

    news.to_csv(cache_path, index_label="Date")
    return news


def download_market_news(
    start: str,
    end: str,
    query: str = DEFAULT_MARKET_QUERY,
    pause_seconds: float = 0.6,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for window_start, window_end in _year_windows(start, end):
        volume = fetch_timeline(query, "timelinevolraw", window_start, window_end)
        time.sleep(pause_seconds)
        tone = fetch_timeline(query, "timelinetone", window_start, window_end)
        time.sleep(pause_seconds)
        frames.append(_daily_features(volume, tone))

    if not frames:
        return neutral_market_news(start, end)

    data = pd.concat(frames).sort_index()
    data = data[~data.index.duplicated(keep="last")]
    return _add_rolling_news_features(data)


def fetch_timeline(query: str, mode: str, start: str, end: str) -> pd.DataFrame:
    params = {
        "query": query,
        "mode": mode,
        "format": "json",
        "startdatetime": _gdelt_datetime(start, start_of_day=True),
        "enddatetime": _gdelt_datetime(end, start_of_day=False),
        "timelinesmooth": "0",
    }
    payload = _fetch_json(f"{GDELT_DOC_ENDPOINT}?{urlencode(params)}")
    timeline = payload.get("timeline", [])
    if not timeline:
        return pd.DataFrame(columns=["date", "value", "norm"])

    data = timeline[0].get("data", [])
    rows = []
    for item in data:
        rows.append(
            {
                "date": pd.to_datetime(item.get("date"), utc=True).tz_convert(None),
                "value": float(item.get("value", 0) or 0),
                "norm": float(item.get("norm", 0) or 0),
            }
        )
    return pd.DataFrame(rows)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _fetch_json(url: str, timeout: int = 60) -> dict[str, object]:
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed official GDELT endpoint.
        return json.loads(response.read().decode("utf-8"))


def _daily_features(volume: pd.DataFrame, tone: pd.DataFrame) -> pd.DataFrame:
    if volume.empty and tone.empty:
        return pd.DataFrame()

    vol = volume.copy()
    if not vol.empty:
        vol["Date"] = vol["date"].dt.floor("D")
        daily_volume = vol.groupby("Date", as_index=True).agg(
            news_market_article_count=("value", "sum"),
            news_market_norm_count=("norm", "sum"),
        )
    else:
        daily_volume = pd.DataFrame()

    tone_data = tone.copy()
    if not tone_data.empty:
        tone_data["Date"] = tone_data["date"].dt.floor("D")
        daily_tone = tone_data.groupby("Date", as_index=True).agg(news_market_avg_tone=("value", "mean"))
    else:
        daily_tone = pd.DataFrame()

    daily = daily_volume.join(daily_tone, how="outer").fillna(0)
    norm = daily["news_market_norm_count"].replace(0, pd.NA)
    daily["news_market_volume_share"] = (daily["news_market_article_count"] / norm).fillna(0)
    daily["news_market_tone_abs"] = daily["news_market_avg_tone"].abs()
    daily.index = pd.to_datetime(daily.index).normalize()
    return daily


def _add_rolling_news_features(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy().sort_index()
    for column in ["news_market_article_count", "news_market_volume_share", "news_market_avg_tone"]:
        output[f"{column}_3d"] = output[column].rolling(3, min_periods=1).mean()
    output["news_market_stress"] = output["news_market_volume_share_3d"] * output["news_market_avg_tone_3d"].clip(upper=0).abs()
    return output.fillna(0)


def neutral_market_news(start: str, end: str) -> pd.DataFrame:
    idx = pd.date_range(start, end, freq="D")
    columns = [
        "news_market_article_count",
        "news_market_norm_count",
        "news_market_volume_share",
        "news_market_avg_tone",
        "news_market_tone_abs",
        "news_market_article_count_3d",
        "news_market_volume_share_3d",
        "news_market_avg_tone_3d",
        "news_market_stress",
    ]
    return pd.DataFrame(0.0, index=idx, columns=columns)


def _read_cached(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    data.index = pd.to_datetime(data.index).normalize()
    return data


def _covers_range(data: pd.DataFrame, start: str, end: str) -> bool:
    if data.empty:
        return False
    return data.index.min() <= pd.Timestamp(start) and data.index.max() >= pd.Timestamp(end)


def _year_windows(start: str, end: str) -> list[tuple[str, str]]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    windows = []
    cursor = start_ts
    while cursor <= end_ts:
        year_end = min(pd.Timestamp(year=cursor.year, month=12, day=31), end_ts)
        windows.append((cursor.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d")))
        cursor = year_end + pd.Timedelta(days=1)
    return windows


def _gdelt_datetime(value: str, start_of_day: bool) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    suffix = "000000" if start_of_day else "235959"
    return parsed.strftime("%Y%m%d") + suffix
