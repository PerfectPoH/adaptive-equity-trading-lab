from __future__ import annotations

import random
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SmallCapBenchmarkConfig:
    holding_period_bars: int = 5
    random_seed: int = 42


@dataclass(frozen=True)
class SmallCapBootstrapRandomBaselineConfig:
    simulations: int = 1000
    base_seed: int = 700
    holding_period_bars: int = 5


BENCHMARK_ORDER = [
    "cash_flat",
    "iwm_proxy",
    "equal_weight_universe",
    "random_entry_baseline",
    "ticker_holding_window",
]


def build_small_cap_benchmark_report(
    candidate_export: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    iwm_frame: pd.DataFrame | None = None,
    config: SmallCapBenchmarkConfig = SmallCapBenchmarkConfig(),
) -> pd.DataFrame:
    if config.holding_period_bars <= 0:
        raise ValueError("holding_period_bars must be positive")

    all_candidate_dates = _candidate_dates(candidate_export)
    operational_candidates = _operational_candidates(candidate_export)
    start, end = _benchmark_window(all_candidate_dates, frames, config.holding_period_bars)

    rows = [
        _row("cash_flat", 0.0, len(all_candidate_dates), "Cash/flat baseline over candidate dates."),
        _row("iwm_proxy", *_window_return(iwm_frame, start, end), description="IWM/Russell 2000 proxy close-to-close return."),
        _row(
            "equal_weight_universe",
            *_equal_weight_universe_return(frames, start, end),
            description="Equal-weight close-to-close return across available universe frames.",
        ),
        _row(
            "random_entry_baseline",
            *_random_entry_return(candidate_export, frames, config),
            description="Seeded random long entries using candidate dates and available universe symbols.",
        ),
        _row(
            "ticker_holding_window",
            *_candidate_holding_return(operational_candidates, frames, config.holding_period_bars),
            description="Average holding-window return for operational candidate tickers.",
        ),
    ]
    report = pd.DataFrame(rows)
    return report.sort_values("benchmark", key=lambda series: series.map({name: i for i, name in enumerate(BENCHMARK_ORDER)})).reset_index(drop=True)


def build_bootstrap_random_baseline_report(
    candidate_export: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    config: SmallCapBootstrapRandomBaselineConfig = SmallCapBootstrapRandomBaselineConfig(),
) -> dict[str, float | int]:
    if config.simulations <= 0:
        raise ValueError("simulations must be positive")
    if config.holding_period_bars <= 0:
        raise ValueError("holding_period_bars must be positive")

    returns: list[float] = []
    observations: list[int] = []
    candidate_dates, symbols, return_lookup = _precompute_random_entry_returns(candidate_export, frames, config.holding_period_bars)
    for seed in range(config.base_seed, config.base_seed + config.simulations):
        value, count = _random_entry_return_from_lookup(candidate_dates, symbols, return_lookup, seed)
        if pd.notna(value):
            returns.append(float(value))
        observations.append(int(count))

    series = pd.Series(returns, dtype=float)
    obs_series = pd.Series(observations, dtype=int)
    if series.empty:
        return {
            "simulations": int(config.simulations),
            "base_seed": int(config.base_seed),
            "seed_start": int(config.base_seed),
            "seed_end": int(config.base_seed + config.simulations - 1),
            "mean_return": float("nan"),
            "median_return": float("nan"),
            "std_return": float("nan"),
            "p05_return": float("nan"),
            "p95_return": float("nan"),
            "observations_per_simulation_min": int(obs_series.min()) if not obs_series.empty else 0,
            "observations_per_simulation_max": int(obs_series.max()) if not obs_series.empty else 0,
            "valid_simulations": 0,
        }
    return {
        "simulations": int(config.simulations),
        "base_seed": int(config.base_seed),
        "seed_start": int(config.base_seed),
        "seed_end": int(config.base_seed + config.simulations - 1),
        "mean_return": float(series.mean()),
        "median_return": float(series.median()),
        "std_return": float(series.std(ddof=1)) if len(series) > 1 else float("nan"),
        "p05_return": float(series.quantile(0.05)),
        "p95_return": float(series.quantile(0.95)),
        "observations_per_simulation_min": int(obs_series.min()) if not obs_series.empty else 0,
        "observations_per_simulation_max": int(obs_series.max()) if not obs_series.empty else 0,
        "valid_simulations": int(len(series)),
    }


def _row(benchmark: str, benchmark_return: float, observations: int, description: str) -> dict[str, object]:
    return {
        "benchmark": benchmark,
        "return": float(benchmark_return),
        "observations": int(observations),
        "description": description,
    }


def _precompute_random_entry_returns(
    candidate_export: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    holding_period_bars: int,
) -> tuple[list[pd.Timestamp], list[str], dict[tuple[pd.Timestamp, str], float]]:
    if candidate_export.empty or "as_of" not in candidate_export.columns or not frames:
        return [], [], {}
    candidate_dates = [date.normalize() for date in pd.to_datetime(candidate_export["as_of"], errors="coerce").dropna().tolist()]
    symbols = sorted(frames)
    unique_dates = sorted(set(candidate_dates))
    return_lookup: dict[tuple[pd.Timestamp, str], float] = {}
    for date in unique_dates:
        for symbol in symbols:
            return_lookup[(date, symbol)] = _holding_return(frames[symbol], date, holding_period_bars)
    return candidate_dates, symbols, return_lookup


def _random_entry_return_from_lookup(
    candidate_dates: list[pd.Timestamp],
    symbols: list[str],
    return_lookup: dict[tuple[pd.Timestamp, str], float],
    random_seed: int,
) -> tuple[float, int]:
    if not candidate_dates or not symbols:
        return float("nan"), 0
    rng = random.Random(random_seed)
    returns: list[float] = []
    for as_of in candidate_dates:
        symbol = rng.choice(symbols)
        value = return_lookup.get((as_of, symbol), float("nan"))
        if pd.notna(value):
            returns.append(float(value))
    if not returns:
        return float("nan"), 0
    return float(sum(returns) / len(returns)), len(returns)


def _candidate_dates(candidate_export: pd.DataFrame) -> list[pd.Timestamp]:
    if "as_of" not in candidate_export.columns or candidate_export.empty:
        return []
    dates = pd.to_datetime(candidate_export["as_of"], errors="coerce").dropna()
    return sorted(dates.dt.normalize().unique())


def _operational_candidates(candidate_export: pd.DataFrame) -> pd.DataFrame:
    if candidate_export.empty or "operational_candidate" not in candidate_export.columns:
        return pd.DataFrame(columns=candidate_export.columns)
    return candidate_export[candidate_export["operational_candidate"].fillna(False).astype(bool)].copy()


def _benchmark_window(
    candidate_dates: list[pd.Timestamp],
    frames: dict[str, pd.DataFrame],
    holding_period_bars: int,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    if not candidate_dates:
        return None, None
    start = candidate_dates[0]
    end_candidates = [_holding_end_index(frame, start, holding_period_bars) for frame in frames.values()]
    end_candidates = [date for date in end_candidates if date is not None]
    if not end_candidates:
        return start, None
    return start, max(end_candidates)


def _window_return(frame: pd.DataFrame | None, start: pd.Timestamp | None, end: pd.Timestamp | None) -> tuple[float, int]:
    if frame is None or frame.empty or start is None or end is None or "Close" not in frame.columns:
        return float("nan"), 0
    data = frame.copy().sort_index()
    start_idx = _nearest_index_on_or_after(data, start)
    end_idx = _nearest_index_on_or_before(data, end)
    if start_idx is None or end_idx is None or data.index.get_loc(end_idx) <= data.index.get_loc(start_idx):
        return float("nan"), 0
    return _close_return(data, start_idx, end_idx), 1


def _equal_weight_universe_return(
    frames: dict[str, pd.DataFrame],
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> tuple[float, int]:
    returns = [_window_return(frame, start, end)[0] for frame in frames.values()]
    clean = [value for value in returns if pd.notna(value)]
    if not clean:
        return float("nan"), 0
    return float(sum(clean) / len(clean)), len(clean)


def _random_entry_return(
    candidate_export: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    config: SmallCapBenchmarkConfig,
) -> tuple[float, int]:
    if candidate_export.empty or "as_of" not in candidate_export.columns or not frames:
        return float("nan"), 0
    symbols = sorted(frames)
    rng = random.Random(config.random_seed)
    returns: list[float] = []
    for _, row in candidate_export.iterrows():
        as_of = pd.to_datetime(row.get("as_of"), errors="coerce")
        if pd.isna(as_of):
            continue
        symbol = rng.choice(symbols)
        value = _holding_return(frames[symbol], as_of.normalize(), config.holding_period_bars)
        if pd.notna(value):
            returns.append(value)
    if not returns:
        return float("nan"), 0
    return float(sum(returns) / len(returns)), len(returns)


def _candidate_holding_return(
    candidates: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    holding_period_bars: int,
) -> tuple[float, int]:
    returns: list[float] = []
    for _, row in candidates.iterrows():
        symbol = str(row.get("symbol", ""))
        as_of = pd.to_datetime(row.get("as_of"), errors="coerce")
        if not symbol or symbol not in frames or pd.isna(as_of):
            continue
        value = _holding_return(frames[symbol], as_of.normalize(), holding_period_bars)
        if pd.notna(value):
            returns.append(value)
    if not returns:
        return float("nan"), 0
    return float(sum(returns) / len(returns)), len(returns)


def _holding_return(frame: pd.DataFrame, as_of: pd.Timestamp, holding_period_bars: int) -> float:
    if frame.empty or "Close" not in frame.columns:
        return float("nan")
    data = frame.copy().sort_index()
    start_idx = _nearest_index_on_or_after(data, as_of)
    if start_idx is None:
        return float("nan")
    end_idx = _holding_end_index(data, start_idx, holding_period_bars)
    if end_idx is None:
        return float("nan")
    return _close_return(data, start_idx, end_idx)


def _holding_end_index(frame: pd.DataFrame, start: pd.Timestamp, holding_period_bars: int) -> pd.Timestamp | None:
    data = frame.copy().sort_index()
    if data.empty:
        return None
    start_idx = _nearest_index_on_or_after(data, start)
    if start_idx is None:
        return None
    start_position = data.index.get_loc(start_idx)
    end_position = start_position + holding_period_bars
    if end_position >= len(data):
        return None
    return data.index[end_position]


def _nearest_index_on_or_after(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    candidates = frame.index[frame.index >= date]
    if len(candidates) == 0:
        return None
    return candidates[0]


def _nearest_index_on_or_before(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    candidates = frame.index[frame.index <= date]
    if len(candidates) == 0:
        return None
    return candidates[-1]


def _close_return(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float:
    start_close = float(frame.loc[start, "Close"])
    end_close = float(frame.loc[end, "Close"])
    if start_close == 0:
        return float("nan")
    return float((end_close / start_close) - 1)
