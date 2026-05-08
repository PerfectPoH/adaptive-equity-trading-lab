from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from src.data.snapshot import latest_snapshot, save_snapshot


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
LOGGER = logging.getLogger(__name__)


@dataclass
class DataValidationResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _flatten_yfinance_columns(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if not isinstance(frame.columns, pd.MultiIndex):
        return frame

    levels = frame.columns.names
    if symbol in frame.columns.get_level_values(0):
        return frame[symbol].copy()
    if symbol in frame.columns.get_level_values(-1):
        return frame.xs(symbol, axis=1, level=-1).copy()

    flattened = frame.copy()
    flattened.columns = [col[0] for col in flattened.columns]
    return flattened


def normalize_ohlcv(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    data = _flatten_yfinance_columns(frame, symbol)
    data = data.rename(columns={col: str(col).title() for col in data.columns})
    data = data[[col for col in data.columns if col in REQUIRED_COLUMNS or col == "Adj Close"]]
    data = data.sort_index()
    data = data[~data.index.duplicated(keep="last")]
    data.index = pd.to_datetime(data.index).tz_localize(None)
    return data


def validate_ohlcv(
    frame: pd.DataFrame,
    min_bars: int = 500,
    max_nan_fraction: float = 0.02,
    max_calendar_gap_days: int = 14,
) -> DataValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")

    if len(frame) < min_bars:
        errors.append(f"Expected at least {min_bars} bars, got {len(frame)}")

    if not frame.index.is_monotonic_increasing:
        errors.append("Date index is not sorted")

    if frame.index.has_duplicates:
        errors.append("Date index has duplicates")

    if not missing_cols and len(frame) > 0:
        nan_fraction = frame[REQUIRED_COLUMNS].isna().mean().max()
        if nan_fraction > max_nan_fraction:
            errors.append(f"NaN fraction too high: {nan_fraction:.3f}")

        gaps = frame.index.to_series().diff().dt.days.dropna()
        if not gaps.empty and int(gaps.max()) > max_calendar_gap_days:
            warnings.append(f"Large calendar gap detected: {int(gaps.max())} days")

        zero_volume_fraction = (frame["Volume"] <= 0).mean()
        if zero_volume_fraction > max_nan_fraction:
            warnings.append(f"High zero-volume fraction: {zero_volume_fraction:.3f}")

    return DataValidationResult(ok=not errors, warnings=warnings, errors=errors)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def download_ticker(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(
        symbol,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        actions=False,
        threads=False,
    )
    if raw.empty:
        raise ValueError(f"No data returned for {symbol}")
    return normalize_ohlcv(raw, symbol)


def download_universe(
    symbols: list[str],
    start: str = "2018-01-01",
    end: str | None = None,
    snapshot_dir: Path | str = "data/snapshots",
    min_bars: int = 500,
    pause_seconds: float = 0.5,
) -> dict[str, pd.DataFrame]:
    successful: dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        try:
            frame = download_ticker(symbol, start=start, end=end)
            validation = validate_ohlcv(frame, min_bars=min_bars)
            for warning in validation.warnings:
                LOGGER.warning("%s: %s", symbol, warning)
            if not validation.ok:
                LOGGER.error("%s failed validation: %s", symbol, "; ".join(validation.errors))
                fallback = load_latest_snapshot(symbol, snapshot_dir=snapshot_dir, min_bars=min_bars)
                if fallback is not None:
                    successful[symbol] = fallback
                continue

            save_snapshot(symbol, frame, snapshot_dir=snapshot_dir)
            successful[symbol] = frame
        except Exception as exc:  # noqa: BLE001 - downloader should keep the universe moving.
            LOGGER.exception("Failed downloading %s: %s", symbol, exc)
            fallback = load_latest_snapshot(symbol, snapshot_dir=snapshot_dir, min_bars=min_bars)
            if fallback is not None:
                successful[symbol] = fallback
        finally:
            time.sleep(pause_seconds)

    return successful


def load_latest_snapshot(
    symbol: str,
    snapshot_dir: Path | str = "data/snapshots",
    min_bars: int = 500,
) -> pd.DataFrame | None:
    path = latest_snapshot(symbol, snapshot_dir=snapshot_dir)
    if path is None:
        LOGGER.error("%s has no local snapshot fallback", symbol)
        return None

    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame = normalize_ohlcv(frame, symbol)
    validation = validate_ohlcv(frame, min_bars=min_bars)
    if not validation.ok:
        LOGGER.error("%s snapshot fallback failed validation: %s", symbol, "; ".join(validation.errors))
        return None
    LOGGER.warning("%s loaded from local snapshot fallback: %s", symbol, path)
    return frame
