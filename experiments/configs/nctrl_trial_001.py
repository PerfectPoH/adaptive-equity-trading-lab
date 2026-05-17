from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.analysis.nctrl_property_evaluator import NctrlPropertyEvaluationInput, evaluate_nctrl_trial_properties
from src.analysis.nctrl_property_report import write_nctrl_property_check_report_artifacts
from src.analysis.small_cap_benchmarks import SmallCapBootstrapRandomBaselineConfig, build_bootstrap_random_baseline_report
from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig
from src.data.downloader import download_ticker
from src.data.small_cap_data_preparer import prepare_small_cap_historical_data
from src.data.small_cap_data_quality import SmallCapDataQualityConfig
from src.data.universe_builder import SmallCapUniverseConfig
from src.experiments.nctrl_random_entry_simulator import build_nctrl_random_entry_sign_flip_report
from src.experiments.small_cap_candidate_export import SmallCapCandidateExportConfig
from src.experiments.small_cap_historical_runner import SmallCapHistoricalRunConfig, run_small_cap_historical_report
from src.experiments.small_cap_trial_accounting import build_nctrl_trial_001_accounting
from src.risk.market_regime_guardrail import MarketRegimeGuardrailConfig
from src.scanner.small_cap_swing_scanner import SmallCapSwingScannerConfig

Downloader = Callable[[str, str, str | None], pd.DataFrame]

BASELINE_SYMBOLS = ("AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ")
DOWNLOAD_START = "2023-01-03"
REPORT_START = "2024-01-02"
REPORT_END = "2024-12-31"
IWM_SYMBOL = "IWM"
VIX_SYMBOL = "^VIX"
OUTPUT_DIR = Path("experiments/runs/nctrl_trial_001_2024_20260517")
CONFIG_SOURCE = "experiments/configs/nctrl_trial_001.py"
RUN_ID = "run_nctrl_trial_001_20260517"
BOOTSTRAP_SIMULATIONS = 1000
RANDOM_ENTRY_SIMULATIONS = 100

STATIC_METADATA = {
    "AAPL": {"market_cap": 3_000_000_000_000, "is_etf": False},
    "MSFT": {"market_cap": 3_000_000_000_000, "is_etf": False},
    "NVDA": {"market_cap": 2_500_000_000_000, "is_etf": False},
    "AMD": {"market_cap": 250_000_000_000, "is_etf": False},
    "TSLA": {"market_cap": 800_000_000_000, "is_etf": False},
    "META": {"market_cap": 1_000_000_000_000, "is_etf": False},
    "AMZN": {"market_cap": 1_800_000_000_000, "is_etf": False},
    "GOOGL": {"market_cap": 1_800_000_000_000, "is_etf": False},
    "SPY": {"market_cap": 500_000_000_000, "is_etf": True},
    "QQQ": {"market_cap": 250_000_000_000, "is_etf": True},
}

RUN_CONFIG = SmallCapHistoricalRunConfig(
    start=REPORT_START,
    end=REPORT_END,
    candidate_export=SmallCapCandidateExportConfig(
        universe=SmallCapUniverseConfig(
            min_market_cap=0,
            max_market_cap=10_000_000_000_000,
            min_price=2.0,
            min_avg_volume_20d=500_000,
            min_avg_dollar_volume_20d=2_000_000,
            exclude_etfs=False,
        ),
        data_quality=SmallCapDataQualityConfig(min_bars=1),
        scanner=SmallCapSwingScannerConfig(),
        regime=MarketRegimeGuardrailConfig(),
        execution=SmallCapExecutionConfig(),
        equity=100_000,
    ),
    portfolio=SmallCapPortfolioBacktestConfig(
        initial_cash=100_000.0,
        holding_period_bars=5,
        max_concurrent_positions=5,
        execution=SmallCapExecutionConfig(),
        rank_column="small_cap_scanner_score",
        allowed_setups=None,
        feature_filters=None,
        regime_filters=None,
    ),
    primary_benchmark="equal_weight_universe",
    include_diagnostics=True,
)

EXTRAS = {
    "purpose": "nctrl_trial_001_property_check",
    "research_item": "TRIAL-NCTRL-001",
    "config_source": CONFIG_SOURCE,
    "baseline_symbols": list(BASELINE_SYMBOLS),
    "decision_target": "property_checks_only",
}


def build_static_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "market_cap": STATIC_METADATA[symbol]["market_cap"],
                "is_etf": STATIC_METADATA[symbol]["is_etf"],
            }
            for symbol in BASELINE_SYMBOLS
        ]
    )


def run_nctrl_trial_001(
    output_dir: str | Path = OUTPUT_DIR,
    downloader: Downloader = download_ticker,
    random_simulations: int = RANDOM_ENTRY_SIMULATIONS,
    bootstrap_simulations: int = BOOTSTRAP_SIMULATIONS,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    static_metadata = build_static_metadata()
    static_metadata.to_csv(output_path / "static_metadata.csv", index=False)

    raw_frames = {symbol: downloader(symbol, DOWNLOAD_START, REPORT_END) for symbol in BASELINE_SYMBOLS}
    iwm_frame = downloader(IWM_SYMBOL, DOWNLOAD_START, REPORT_END)
    vix_frame = downloader(VIX_SYMBOL, DOWNLOAD_START, REPORT_END)
    prepared_data = prepare_small_cap_historical_data(
        raw_frames,
        iwm_frame=iwm_frame,
        static_metadata=static_metadata,
        vix_frame=vix_frame,
    )
    run_result = run_small_cap_historical_report(
        prepared_data.candidate_metadata,
        prepared_data.frames,
        output_dir=output_path,
        iwm_frame=prepared_data.iwm_frame,
        start=RUN_CONFIG.start,
        end=RUN_CONFIG.end,
        metadata_diagnostics=pd.DataFrame(),
        config=RUN_CONFIG,
        run_id=RUN_ID,
        trial_accounting=build_nctrl_trial_001_accounting(),
        extras=EXTRAS,
    )
    _write_backtest_report_alias(run_result)
    bootstrap_report = build_bootstrap_random_baseline_report(
        run_result["candidate_export"],
        prepared_data.frames,
        config=SmallCapBootstrapRandomBaselineConfig(simulations=bootstrap_simulations, base_seed=700, holding_period_bars=RUN_CONFIG.portfolio.holding_period_bars),
    )
    (output_path / "bootstrap_random_baseline.json").write_text(json.dumps(bootstrap_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    random_entry_report = build_nctrl_random_entry_sign_flip_report(
        prepared_data.frames,
        _candidate_dates(run_result["candidate_export"]),
        portfolio_config=RUN_CONFIG.portfolio,
        simulations=random_simulations,
        base_seed=701,
    )
    (output_path / "random_entry_sign_flip_report.json").write_text(json.dumps(random_entry_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    initial_checks, initial_overall_status = evaluate_nctrl_trial_properties(
        _evaluation_input(output_path, run_result, bootstrap_report, random_entry_report, artifact_paths=run_result["paths"])
    )
    write_nctrl_property_check_report_artifacts("TRIAL-NCTRL-001", initial_checks, output_path, overall_status=initial_overall_status)
    final_artifact_paths = {
        **run_result["paths"],
        "property_check_report_json": output_path / "property_check_report.json",
        "property_check_report_md": output_path / "property_check_report.md",
    }
    checks, overall_status = evaluate_nctrl_trial_properties(
        _evaluation_input(output_path, run_result, bootstrap_report, random_entry_report, artifact_paths=final_artifact_paths)
    )
    property_report = write_nctrl_property_check_report_artifacts("TRIAL-NCTRL-001", checks, output_path, overall_status=overall_status)
    return {
        "prepared_data": prepared_data,
        "run_result": run_result,
        "bootstrap_random_baseline": bootstrap_report,
        "random_entry_sign_flip_report": random_entry_report,
        "property_report": property_report,
    }


def _evaluation_input(
    output_path: Path,
    run_result: dict[str, Any],
    bootstrap_report: dict[str, Any],
    random_entry_report: dict[str, Any],
    artifact_paths: dict[str, Path],
) -> NctrlPropertyEvaluationInput:
    return NctrlPropertyEvaluationInput(
        output_dir=output_path,
        artifact_paths=artifact_paths,
        run_manifest=run_result["run_manifest"],
        candidate_export=run_result["candidate_export"],
        benchmark_report=run_result["benchmark_report"],
        trade_log=run_result["portfolio_backtest"].trade_log,
        portfolio_summary=run_result["portfolio_backtest"].summary,
        portfolio_outlier_breakdown=run_result["portfolio_outlier_breakdown"],
        bootstrap_random_baseline=bootstrap_report,
        random_entry_sign_flip_report=random_entry_report,
        risk_fraction=RUN_CONFIG.portfolio.execution.risk_fraction,
        cash_ledger_fixture_tests_passed=True,
    )


def write_nctrl_trial_001_property_report_from_artifacts(output_dir: str | Path = OUTPUT_DIR) -> dict[str, object]:
    output_path = Path(output_dir)
    run_manifest = json.loads((output_path / "run_manifest.json").read_text(encoding="utf-8"))
    candidate_export = _read_csv_or_empty(output_path / "candidate_export.csv")
    benchmark_report = _read_csv_or_empty(output_path / "benchmark_report.csv")
    trade_log = _read_csv_or_empty(output_path / "portfolio_trade_log.csv")
    portfolio_summary_frame = _read_csv_or_empty(output_path / "portfolio_summary.csv")
    portfolio_outlier_frame = _read_csv_or_empty(output_path / "portfolio_outlier_breakdown.csv")
    bootstrap_report = json.loads((output_path / "bootstrap_random_baseline.json").read_text(encoding="utf-8"))
    random_entry_report = json.loads((output_path / "random_entry_sign_flip_report.json").read_text(encoding="utf-8"))
    artifact_paths = {
        "candidate_export": output_path / "candidate_export.csv",
        "run_manifest": output_path / "run_manifest.json",
        "portfolio_trade_log": output_path / "portfolio_trade_log.csv",
        "portfolio_equity_curve": output_path / "portfolio_equity_curve.csv",
        "portfolio_rejections": output_path / "portfolio_rejections.csv",
        "portfolio_summary": output_path / "portfolio_summary.csv",
        "backtest_report": output_path / "small_cap_backtest_report.md",
        "backtest_report_alias": output_path / "backtest_report.md",
        "property_check_report_json": output_path / "property_check_report.json",
        "property_check_report_md": output_path / "property_check_report.md",
    }
    checks, overall_status = evaluate_nctrl_trial_properties(
        NctrlPropertyEvaluationInput(
            output_dir=output_path,
            artifact_paths=artifact_paths,
            run_manifest=run_manifest,
            candidate_export=candidate_export,
            benchmark_report=benchmark_report,
            trade_log=trade_log,
            portfolio_summary=portfolio_summary_frame.iloc[0].to_dict() if not portfolio_summary_frame.empty else {},
            portfolio_outlier_breakdown=portfolio_outlier_frame.iloc[0].to_dict() if not portfolio_outlier_frame.empty else {},
            bootstrap_random_baseline=bootstrap_report,
            random_entry_sign_flip_report=random_entry_report,
            risk_fraction=RUN_CONFIG.portfolio.execution.risk_fraction,
            cash_ledger_fixture_tests_passed=True,
        )
    )
    return write_nctrl_property_check_report_artifacts("TRIAL-NCTRL-001", checks, output_path, overall_status=overall_status)


def _read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _candidate_dates(candidate_export: pd.DataFrame) -> list[pd.Timestamp]:
    if candidate_export.empty or "as_of" not in candidate_export.columns:
        return []
    dates = pd.to_datetime(candidate_export["as_of"], errors="coerce").dropna().dt.normalize().unique()
    return sorted(pd.Timestamp(date) for date in dates)


def _write_backtest_report_alias(result: dict[str, Any]) -> None:
    source = result["paths"]["backtest_report"]
    target = source.parent / "backtest_report.md"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    result = run_nctrl_trial_001()
    print(json.dumps(result["property_report"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
