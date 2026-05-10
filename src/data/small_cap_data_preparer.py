from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.features.feature_pipeline import build_features
from src.features.indicators import ema


STATIC_METADATA_REQUIRED_COLUMNS = ("symbol", "market_cap", "is_etf")
CANDIDATE_METADATA_COLUMNS = (
    "symbol",
    "market_cap",
    "price",
    "avg_volume_20d",
    "avg_dollar_volume_20d",
    "is_etf",
)


@dataclass(frozen=True)
class SmallCapPreparedData:
    candidate_metadata: pd.DataFrame
    frames: dict[str, pd.DataFrame]
    iwm_frame: pd.DataFrame
    diagnostics: dict[str, list[str]]


def prepare_small_cap_historical_data(
    raw_frames: dict[str, pd.DataFrame],
    iwm_frame: pd.DataFrame,
    static_metadata: pd.DataFrame,
    vix_frame: pd.DataFrame | None = None,
) -> SmallCapPreparedData:
    _validate_static_metadata(static_metadata)
    metadata = static_metadata.copy()
    metadata["symbol"] = metadata["symbol"].astype(str)
    iwm = iwm_frame.copy().sort_index()
    vix = vix_frame.copy().sort_index() if vix_frame is not None else None
    diagnostics = _diagnostics(metadata, raw_frames)

    prepared_frames: dict[str, pd.DataFrame] = {}
    metadata_rows: list[dict[str, object]] = []
    for _, row in metadata.iterrows():
        symbol = str(row["symbol"])
        frame = raw_frames.get(symbol)
        if frame is None or frame.empty:
            continue
        prepared = _prepare_symbol_frame(frame, iwm, vix)
        prepared_frames[symbol] = prepared
        metadata_rows.append(_candidate_metadata_row(symbol, row, prepared))

    candidate_metadata = pd.DataFrame(metadata_rows, columns=CANDIDATE_METADATA_COLUMNS)
    return SmallCapPreparedData(
        candidate_metadata=candidate_metadata,
        frames=prepared_frames,
        iwm_frame=iwm,
        diagnostics=diagnostics,
    )


def _validate_static_metadata(static_metadata: pd.DataFrame) -> None:
    missing = [column for column in STATIC_METADATA_REQUIRED_COLUMNS if column not in static_metadata.columns]
    if missing:
        raise ValueError(f"static_metadata missing columns: {missing}")


def _diagnostics(static_metadata: pd.DataFrame, raw_frames: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    static_symbols = set(static_metadata["symbol"].astype(str)) if "symbol" in static_metadata.columns else set()
    return {
        "missing_frame_symbols": sorted(symbol for symbol in static_symbols if symbol not in raw_frames),
        "empty_frame_symbols": sorted(symbol for symbol, frame in raw_frames.items() if frame is None or frame.empty),
        "raw_symbols_without_metadata": sorted(symbol for symbol in raw_frames if symbol not in static_symbols),
    }


def _prepare_symbol_frame(frame: pd.DataFrame, iwm_frame: pd.DataFrame, vix_frame: pd.DataFrame | None) -> pd.DataFrame:
    data = build_features(frame.copy().sort_index())
    dollar_volume = pd.to_numeric(data["Close"], errors="coerce") * pd.to_numeric(data["Volume"], errors="coerce")
    data["avg_volume_20d"] = pd.to_numeric(data["Volume"], errors="coerce").rolling(20, min_periods=20).mean()
    data["avg_dollar_volume_20d"] = dollar_volume.rolling(20, min_periods=20).mean()
    return _add_market_regime_columns(data, iwm_frame, vix_frame)


def _add_market_regime_columns(data: pd.DataFrame, iwm_frame: pd.DataFrame, vix_frame: pd.DataFrame | None) -> pd.DataFrame:
    if iwm_frame.empty or "Close" not in iwm_frame.columns:
        data["iwm_close"] = pd.NA
        data["iwm_ema_50"] = pd.NA
        data["iwm_ema_200"] = pd.NA
    else:
        iwm = iwm_frame.copy().sort_index()
        iwm_close = pd.to_numeric(iwm["Close"], errors="coerce")
        data["iwm_close"] = iwm_close.reindex(data.index).ffill()
        data["iwm_ema_50"] = ema(iwm_close, 50).reindex(data.index).ffill()
        data["iwm_ema_200"] = ema(iwm_close, 200).reindex(data.index).ffill()

    if vix_frame is None or vix_frame.empty or "Close" not in vix_frame.columns:
        data["vix_close"] = pd.NA
    else:
        vix = vix_frame.copy().sort_index()
        data["vix_close"] = pd.to_numeric(vix["Close"], errors="coerce").reindex(data.index).ffill()
    return data


def _candidate_metadata_row(symbol: str, static_row: pd.Series, prepared: pd.DataFrame) -> dict[str, object]:
    latest = prepared.iloc[-1]
    return {
        "symbol": symbol,
        "market_cap": static_row["market_cap"],
        "price": _safe_float(latest.get("Close")),
        "avg_volume_20d": _safe_float(latest.get("avg_volume_20d")),
        "avg_dollar_volume_20d": _safe_float(latest.get("avg_dollar_volume_20d")),
        "is_etf": bool(static_row["is_etf"]),
    }


def _safe_float(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    return float(value)
