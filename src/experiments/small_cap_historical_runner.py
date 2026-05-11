from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis.small_cap_backtest_report import write_small_cap_backtest_report_markdown
from src.analysis.small_cap_benchmarks import SmallCapBenchmarkConfig, build_small_cap_benchmark_report
from src.analysis.small_cap_portfolio_diagnostics import (
    build_cash_starvation_report,
    build_portfolio_outlier_breakdown,
    build_regime_profile_report,
    build_score_profile_report,
    build_setup_cash_starvation_summary,
    build_setup_feature_profile_report,
    build_setup_score_profile_report,
    build_setup_summary_report,
    summarize_cash_starvation_report,
)
from src.backtest.small_cap_portfolio_backtester import (
    SmallCapPortfolioBacktestConfig,
    filter_small_cap_portfolio_candidates,
    run_small_cap_portfolio_backtest,
)
from src.experiments.run_manifest import build_run_manifest, manifest_to_dict, write_run_manifest_json
from src.experiments.small_cap_candidate_export import SmallCapCandidateExportConfig, build_small_cap_candidate_export


@dataclass(frozen=True)
class SmallCapHistoricalRunConfig:
    start: str | pd.Timestamp | None = None
    end: str | pd.Timestamp | None = None
    candidate_export: SmallCapCandidateExportConfig = SmallCapCandidateExportConfig()
    benchmark: SmallCapBenchmarkConfig = SmallCapBenchmarkConfig()
    portfolio: SmallCapPortfolioBacktestConfig = SmallCapPortfolioBacktestConfig()
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
    metadata_diagnostics: pd.DataFrame | None = None,
    config: SmallCapHistoricalRunConfig = SmallCapHistoricalRunConfig(),
    run_id: str | None = None,
    created_at: str | datetime | None = None,
    git_commit: str | None = None,
    host: str | None = None,
    extras: dict[str, Any] | None = None,
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

    universe_symbols = _extract_universe(candidate_metadata)
    period_start, period_end = _format_period(selected_dates)
    manifest = build_run_manifest(
        config,
        universe=universe_symbols,
        period_start=period_start,
        period_end=period_end,
        run_id=run_id,
        created_at=created_at,
        git_commit=git_commit,
        host=host,
        extras=extras,
    )
    manifest_dict = manifest_to_dict(manifest)

    candidate_export = _build_historical_candidate_export(candidate_metadata, frames, selected_dates, config)
    benchmark_report = build_small_cap_benchmark_report(
        candidate_export,
        frames,
        iwm_frame=iwm_frame,
        config=config.benchmark,
    )
    portfolio_filtered_candidate_export = filter_small_cap_portfolio_candidates(candidate_export, config.portfolio)
    portfolio_filtered_benchmark_report = build_small_cap_benchmark_report(
        portfolio_filtered_candidate_export,
        frames,
        iwm_frame=iwm_frame,
        config=config.benchmark,
    )
    portfolio_backtest = run_small_cap_portfolio_backtest(candidate_export, frames, config=config.portfolio)
    portfolio_outlier_breakdown = build_portfolio_outlier_breakdown(
        portfolio_backtest.trade_log,
        initial_cash=portfolio_backtest.summary.get("initial_cash"),
    )
    portfolio_score_profile = build_score_profile_report(portfolio_backtest.trade_log)
    portfolio_cash_starvation = build_cash_starvation_report(
        portfolio_backtest.rejections,
        frames,
        holding_period_bars=config.portfolio.holding_period_bars,
    )
    portfolio_cash_starvation_summary = summarize_cash_starvation_report(
        portfolio_cash_starvation,
        total_insufficient_funds_rejections=portfolio_backtest.rejection_summary.get("insufficient_funds", 0),
    )
    portfolio_setup_summary = build_setup_summary_report(portfolio_backtest.trade_log)
    portfolio_setup_score_profile = build_setup_score_profile_report(portfolio_backtest.trade_log)
    portfolio_setup_cash_starvation_summary = build_setup_cash_starvation_summary(portfolio_cash_starvation)
    portfolio_setup_feature_profile = build_setup_feature_profile_report(portfolio_backtest.trade_log)
    portfolio_regime_profile = build_regime_profile_report(portfolio_backtest.trade_log)

    candidate_path = output_path / "candidate_export.csv"
    benchmark_path = output_path / "benchmark_report.csv"
    portfolio_filtered_candidate_path = output_path / "portfolio_filtered_candidate_export.csv"
    portfolio_filtered_benchmark_path = output_path / "portfolio_filtered_benchmark_report.csv"
    portfolio_trade_log_path = output_path / "portfolio_trade_log.csv"
    portfolio_equity_curve_path = output_path / "portfolio_equity_curve.csv"
    portfolio_rejections_path = output_path / "portfolio_rejections.csv"
    portfolio_summary_path = output_path / "portfolio_summary.csv"
    portfolio_outlier_breakdown_path = output_path / "portfolio_outlier_breakdown.csv"
    portfolio_score_profile_path = output_path / "portfolio_score_profile.csv"
    portfolio_cash_starvation_path = output_path / "portfolio_cash_starvation.csv"
    portfolio_cash_starvation_summary_path = output_path / "portfolio_cash_starvation_summary.csv"
    portfolio_setup_summary_path = output_path / "portfolio_setup_summary.csv"
    portfolio_setup_score_profile_path = output_path / "portfolio_setup_score_profile.csv"
    portfolio_setup_cash_starvation_summary_path = output_path / "portfolio_setup_cash_starvation_summary.csv"
    portfolio_setup_feature_profile_path = output_path / "portfolio_setup_feature_profile.csv"
    portfolio_regime_profile_path = output_path / "portfolio_regime_profile.csv"
    run_manifest_path = output_path / "run_manifest.json"
    report_path = output_path / "small_cap_backtest_report.md"
    candidate_export.to_csv(candidate_path, index=False)
    benchmark_report.to_csv(benchmark_path, index=False)
    portfolio_filtered_candidate_export.to_csv(portfolio_filtered_candidate_path, index=False)
    portfolio_filtered_benchmark_report.to_csv(portfolio_filtered_benchmark_path, index=False)
    portfolio_backtest.trade_log.to_csv(portfolio_trade_log_path, index=False)
    portfolio_backtest.equity_curve.to_csv(portfolio_equity_curve_path, index=False)
    portfolio_backtest.rejections.to_csv(portfolio_rejections_path, index=False)
    pd.DataFrame([portfolio_backtest.summary]).to_csv(portfolio_summary_path, index=False)
    pd.DataFrame([portfolio_outlier_breakdown]).to_csv(portfolio_outlier_breakdown_path, index=False)
    portfolio_score_profile.to_csv(portfolio_score_profile_path, index=False)
    portfolio_cash_starvation.to_csv(portfolio_cash_starvation_path, index=False)
    pd.DataFrame([portfolio_cash_starvation_summary]).to_csv(portfolio_cash_starvation_summary_path, index=False)
    portfolio_setup_summary.to_csv(portfolio_setup_summary_path, index=False)
    portfolio_setup_score_profile.to_csv(portfolio_setup_score_profile_path, index=False)
    portfolio_setup_cash_starvation_summary.to_csv(portfolio_setup_cash_starvation_summary_path, index=False)
    portfolio_setup_feature_profile.to_csv(portfolio_setup_feature_profile_path, index=False)
    portfolio_regime_profile.to_csv(portfolio_regime_profile_path, index=False)
    write_run_manifest_json(manifest, run_manifest_path)
    backtest_report = write_small_cap_backtest_report_markdown(
        candidate_export,
        benchmark_report,
        report_path,
        primary_benchmark=config.primary_benchmark,
        metadata_diagnostics=metadata_diagnostics,
        portfolio_filtered_candidate_export=portfolio_filtered_candidate_export,
        portfolio_filtered_benchmark_report=portfolio_filtered_benchmark_report,
        portfolio_summary=portfolio_backtest.summary,
        portfolio_rejection_summary=portfolio_backtest.rejection_summary,
        portfolio_outlier_breakdown=portfolio_outlier_breakdown,
        portfolio_score_profile=portfolio_score_profile,
        portfolio_cash_starvation_summary=portfolio_cash_starvation_summary,
        portfolio_setup_summary=portfolio_setup_summary,
        portfolio_setup_score_profile=portfolio_setup_score_profile,
        portfolio_setup_cash_starvation_summary=portfolio_setup_cash_starvation_summary,
        portfolio_setup_feature_profile=portfolio_setup_feature_profile,
        portfolio_regime_profile=portfolio_regime_profile,
        run_manifest=manifest_dict,
    )

    return {
        "candidate_export": candidate_export,
        "benchmark_report": benchmark_report,
        "portfolio_filtered_candidate_export": portfolio_filtered_candidate_export,
        "portfolio_filtered_benchmark_report": portfolio_filtered_benchmark_report,
        "portfolio_backtest": portfolio_backtest,
        "portfolio_outlier_breakdown": portfolio_outlier_breakdown,
        "portfolio_score_profile": portfolio_score_profile,
        "portfolio_cash_starvation": portfolio_cash_starvation,
        "portfolio_cash_starvation_summary": portfolio_cash_starvation_summary,
        "portfolio_setup_summary": portfolio_setup_summary,
        "portfolio_setup_score_profile": portfolio_setup_score_profile,
        "portfolio_setup_cash_starvation_summary": portfolio_setup_cash_starvation_summary,
        "portfolio_setup_feature_profile": portfolio_setup_feature_profile,
        "portfolio_regime_profile": portfolio_regime_profile,
        "run_manifest": manifest_dict,
        "backtest_report": backtest_report,
        "paths": {
            "candidate_export": candidate_path,
            "benchmark_report": benchmark_path,
            "portfolio_filtered_candidate_export": portfolio_filtered_candidate_path,
            "portfolio_filtered_benchmark_report": portfolio_filtered_benchmark_path,
            "portfolio_trade_log": portfolio_trade_log_path,
            "portfolio_equity_curve": portfolio_equity_curve_path,
            "portfolio_rejections": portfolio_rejections_path,
            "portfolio_summary": portfolio_summary_path,
            "portfolio_outlier_breakdown": portfolio_outlier_breakdown_path,
            "portfolio_score_profile": portfolio_score_profile_path,
            "portfolio_cash_starvation": portfolio_cash_starvation_path,
            "portfolio_cash_starvation_summary": portfolio_cash_starvation_summary_path,
            "portfolio_setup_summary": portfolio_setup_summary_path,
            "portfolio_setup_score_profile": portfolio_setup_score_profile_path,
            "portfolio_setup_cash_starvation_summary": portfolio_setup_cash_starvation_summary_path,
            "portfolio_setup_feature_profile": portfolio_setup_feature_profile_path,
            "portfolio_regime_profile": portfolio_regime_profile_path,
            "run_manifest": run_manifest_path,
            "backtest_report": report_path,
        },
    }


def _extract_universe(candidate_metadata: pd.DataFrame) -> list[str]:
    if "symbol" not in candidate_metadata.columns:
        return []
    symbols = candidate_metadata["symbol"].astype(str).str.strip()
    symbols = [s for s in symbols.tolist() if s]
    seen: set[str] = set()
    ordered: list[str] = []
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        ordered.append(symbol)
    return ordered


def _format_period(selected_dates: list[pd.Timestamp]) -> tuple[str | None, str | None]:
    if not selected_dates:
        return None, None
    start = selected_dates[0]
    end = selected_dates[-1]
    return start.date().isoformat(), end.date().isoformat()


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
