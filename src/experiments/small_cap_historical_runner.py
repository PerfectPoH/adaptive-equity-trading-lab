from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis.small_cap_backtest_report import write_small_cap_backtest_report_markdown
from src.analysis.small_cap_benchmarks import SmallCapBenchmarkConfig, build_small_cap_benchmark_report
from src.experiments.small_cap_candidate_export import SmallCapCandidateExportConfig, build_small_cap_candidate_export


@dataclass(frozen=True)
class SmallCapHistoricalRunConfig:
    start: str | pd.Timestamp | None = None
    end: str | pd.Timestamp | None = None
    candidate_export: SmallCapCandidateExportConfig = SmallCapCandidateExportConfig()
    benchmark: SmallCapBenchmarkConfig = SmallCapBenchmarkConfig()
    primary_benchmark: str = "equal_weight_universe"
    include_diagnostics: bool = True


def run_small_cap_historical_report(
    candidate_metadata: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    output_dir: str | Path,
    iwm_frame: pd.DataFrame | None = None,
    as_of_dates: list[str | pd.Timestamp] | None = None,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    config: SmallCapHistoricalRunConfig = SmallCapHistoricalRunConfig(),
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    selected_dates = _resolve_as_of_dates(
        frames,
        explicit_dates=as_of_dates,
        start=start if start is not None else config.start,
        end=end if end is not None else config.end,
    )
    if not selected_dates:
        raise ValueError("No historical as_of dates available for the requested range")

    candidate_export = _build_historical_candidate_export(candidate_metadata, frames, selected_dates, config)
    benchmark_report = build_small_cap_benchmark_report(
        candidate_export,
        frames,
        iwm_frame=iwm_frame,
        config=config.benchmark,
    )

    candidate_path = output_path / "candidate_export.csv"
    benchmark_path = output_path / "benchmark_report.csv"
    report_path = output_path / "small_cap_backtest_report.md"
    candidate_export.to_csv(candidate_path, index=False)
    benchmark_report.to_csv(benchmark_path, index=False)
    backtest_report = write_small_cap_backtest_report_markdown(
        candidate_export,
        benchmark_report,
        report_path,
        primary_benchmark=config.primary_benchmark,
    )

    return {
        "candidate_export": candidate_export,
        "benchmark_report": benchmark_report,
        "backtest_report": backtest_report,
        "paths": {
            "candidate_export": candidate_path,
            "benchmark_report": benchmark_path,
            "backtest_report": report_path,
        },
    }


def _build_historical_candidate_export(
    candidate_metadata: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    as_of_dates: list[pd.Timestamp],
    config: SmallCapHistoricalRunConfig,
) -> pd.DataFrame:
    exports = [
        build_small_cap_candidate_export(
            candidate_metadata,
            frames,
            as_of=date,
            config=config.candidate_export,
            operational_only=not config.include_diagnostics,
        )
        for date in as_of_dates
    ]
    exports = [export for export in exports if not export.empty]
    if not exports:
        return build_small_cap_candidate_export(
            candidate_metadata,
            frames,
            as_of=as_of_dates[0],
            config=config.candidate_export,
            operational_only=not config.include_diagnostics,
        )
    return pd.concat(exports, ignore_index=True)


def _resolve_as_of_dates(
    frames: dict[str, pd.DataFrame],
    explicit_dates: list[str | pd.Timestamp] | None,
    start: str | pd.Timestamp | None,
    end: str | pd.Timestamp | None,
) -> list[pd.Timestamp]:
    if explicit_dates is not None:
        dates = [pd.Timestamp(date).normalize() for date in explicit_dates]
    else:
        dates = _available_historical_dates(frames)
    start_ts = pd.Timestamp(start).normalize() if start is not None else None
    end_ts = pd.Timestamp(end).normalize() if end is not None else None
    if start_ts is not None:
        dates = [date for date in dates if date >= start_ts]
    if end_ts is not None:
        dates = [date for date in dates if date <= end_ts]
    return sorted(dict.fromkeys(dates))


def _available_historical_dates(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    dates: set[pd.Timestamp] = set()
    for frame in frames.values():
        if frame.empty:
            continue
        ordered_index = pd.DatetimeIndex(frame.sort_index().index).normalize()
        if len(ordered_index) < 2:
            continue
        dates.update(ordered_index[:-1])
    return sorted(dates)
