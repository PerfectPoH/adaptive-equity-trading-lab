from __future__ import annotations

import random
from dataclasses import dataclass

import pandas as pd

from src.experiments.small_cap_candidate_export import EXPORT_COLUMNS


@dataclass(frozen=True)
class NctrlRandomEntrySimulatorConfig:
    seed: int = 701
    candidates_per_day: int = 1
    setup_label: str = "nctrl_random_entry"


def build_nctrl_random_entry_candidate_export(
    frames: dict[str, pd.DataFrame],
    as_of_dates: list[str | pd.Timestamp],
    config: NctrlRandomEntrySimulatorConfig = NctrlRandomEntrySimulatorConfig(),
) -> pd.DataFrame:
    if config.candidates_per_day <= 0:
        raise ValueError("candidates_per_day must be positive")
    symbols = sorted(symbol for symbol, frame in frames.items() if frame is not None and not frame.empty)
    if not symbols:
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    rows: list[dict[str, object]] = []
    rng = random.Random(config.seed)
    for as_of in sorted(pd.Timestamp(date).normalize() for date in as_of_dates):
        selected_symbols = _sample_symbols(symbols, config.candidates_per_day, rng)
        for rank, symbol in enumerate(selected_symbols):
            score = float(config.candidates_per_day - rank) / float(config.candidates_per_day)
            rows.append(_candidate_row(symbol, as_of, score, config.setup_label, frames[symbol]))
    if not rows:
        return pd.DataFrame(columns=EXPORT_COLUMNS)
    export = pd.DataFrame(rows)
    for column in EXPORT_COLUMNS:
        if column not in export.columns:
            export[column] = pd.NA
    return export[EXPORT_COLUMNS].reset_index(drop=True)


def _sample_symbols(symbols: list[str], candidates_per_day: int, rng: random.Random) -> list[str]:
    if candidates_per_day <= len(symbols):
        return rng.sample(symbols, k=candidates_per_day)
    return [rng.choice(symbols) for _ in range(candidates_per_day)]


def _candidate_row(symbol: str, as_of: pd.Timestamp, score: float, setup_label: str, frame: pd.DataFrame) -> dict[str, object]:
    feature_row = _feature_row(frame, as_of)
    return {
        "as_of": as_of.date().isoformat(),
        "symbol": symbol,
        "operational_candidate": True,
        "passes_universe_filter": True,
        "universe_rejection_reasons": "",
        "data_quality_status": "pass",
        "data_quality_warnings": "",
        "data_quality_errors": "",
        "small_cap_setup": setup_label,
        "small_cap_scanner_score": score,
        "small_cap_scanner_pass": True,
        "small_cap_scanner_reject_reason": "",
        "gap_pct": feature_row.get("gap_pct", 0.0),
        "open_to_close_return": feature_row.get("open_to_close_return", 0.0),
        "close_position_daily_range": feature_row.get("close_position_daily_range", pd.NA),
        "intraday_range_pct": feature_row.get("intraday_range_pct", pd.NA),
        "relative_volume_20d": feature_row.get("relative_volume_20d", pd.NA),
        "atr_pct": feature_row.get("atr_pct", pd.NA),
        "distance_from_20d_high": feature_row.get("distance_from_20d_high", pd.NA),
        "rolling_volatility_20d": feature_row.get("rolling_volatility_20d", pd.NA),
        "iwm_close": feature_row.get("iwm_close", pd.NA),
        "iwm_ema_50": feature_row.get("iwm_ema_50", pd.NA),
        "iwm_ema_200": feature_row.get("iwm_ema_200", pd.NA),
        "vix_close": feature_row.get("vix_close", pd.NA),
        "market_regime_trade_allowed": True,
        "market_regime_block_reason": "",
        "small_cap_execution_valid": True,
        "small_cap_execution_skip_reason": "",
        "small_cap_entry_reference_price": feature_row.get("Close", pd.NA),
        "small_cap_entry_price": feature_row.get("Close", pd.NA),
        "small_cap_position_size": pd.NA,
        "small_cap_position_notional": pd.NA,
        "small_cap_max_liquidity_notional": pd.NA,
        "avg_dollar_volume_20d": feature_row.get("avg_dollar_volume_20d", pd.NA),
    }


def _feature_row(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    data = frame.copy().sort_index()
    eligible = data.index[data.index <= as_of]
    if len(eligible) == 0:
        return pd.Series(dtype=object)
    return data.loc[eligible[-1]]
