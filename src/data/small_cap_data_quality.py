from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data.downloader import validate_ohlcv


@dataclass(frozen=True)
class SmallCapDataQualityConfig:
    min_bars: int = 252
    max_nan_fraction: float = 0.02
    max_calendar_gap_days: int = 14
    max_zero_volume_fraction: float = 0.02
    max_abs_daily_return: float = 0.75


def build_small_cap_data_quality_report(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    config: SmallCapDataQualityConfig = SmallCapDataQualityConfig(),
) -> pd.DataFrame:
    rows = [_build_symbol_quality_row(symbol, frames.get(symbol), config) for symbol in symbols]
    return pd.DataFrame(rows)


def _build_symbol_quality_row(
    symbol: str,
    frame: pd.DataFrame | None,
    config: SmallCapDataQualityConfig,
) -> dict[str, object]:
    if frame is None or frame.empty:
        return {
            "symbol": symbol,
            "status": "fail",
            "bars": 0,
            "start": None,
            "end": None,
            "zero_volume_fraction": None,
            "max_abs_daily_return": None,
            "warnings": "",
            "errors": "missing_data",
        }

    validation = validate_ohlcv(
        frame,
        min_bars=config.min_bars,
        max_nan_fraction=config.max_nan_fraction,
        max_calendar_gap_days=config.max_calendar_gap_days,
    )
    warnings = list(validation.warnings)
    errors = list(validation.errors)
    zero_volume_fraction = _zero_volume_fraction(frame)
    max_abs_daily_return = _max_abs_daily_return(frame)

    if zero_volume_fraction is not None and zero_volume_fraction > config.max_zero_volume_fraction:
        warnings.append(f"high_zero_volume_fraction:{zero_volume_fraction:.3f}")
    if max_abs_daily_return is not None and max_abs_daily_return > config.max_abs_daily_return:
        warnings.append(f"extreme_price_jump:{max_abs_daily_return:.3f}")

    status = "fail" if errors else "warn" if warnings else "pass"
    return {
        "symbol": symbol,
        "status": status,
        "bars": int(len(frame)),
        "start": frame.index.min().date().isoformat() if len(frame.index) else None,
        "end": frame.index.max().date().isoformat() if len(frame.index) else None,
        "zero_volume_fraction": zero_volume_fraction,
        "max_abs_daily_return": max_abs_daily_return,
        "warnings": ";".join(warnings),
        "errors": ";".join(errors),
    }


def _zero_volume_fraction(frame: pd.DataFrame) -> float | None:
    if "Volume" not in frame.columns or frame.empty:
        return None
    return float((frame["Volume"] <= 0).mean())


def _max_abs_daily_return(frame: pd.DataFrame) -> float | None:
    if "Close" not in frame.columns or len(frame) < 2:
        return None
    returns = pd.to_numeric(frame["Close"], errors="coerce").pct_change().abs().dropna()
    if returns.empty:
        return None
    return float(returns.max())
