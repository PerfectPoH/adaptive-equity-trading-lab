from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis.small_cap_benchmarks import SmallCapBenchmarkConfig
from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig
from src.data.downloader import download_ticker
from src.data.small_cap_data_preparer import prepare_small_cap_historical_data
from src.data.small_cap_data_quality import SmallCapDataQualityConfig
from src.data.universe_builder import SmallCapUniverseConfig
from src.experiments.small_cap_candidate_export import SmallCapCandidateExportConfig
from src.experiments.small_cap_historical_runner import SmallCapHistoricalRunConfig, run_small_cap_historical_report
from src.risk.market_regime_guardrail import MarketRegimeGuardrailConfig
from src.scanner.small_cap_swing_scanner import SmallCapSwingScannerConfig

BASELINE_SYMBOLS = ("AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ")
DOWNLOAD_START = "2023-01-03"
REPORT_START = "2024-01-02"
REPORT_END = "2024-12-31"
IWM_SYMBOL = "IWM"
VIX_SYMBOL = "^VIX"
OUTPUT_DIR = Path("experiments/runs/nctrl_scaffolding_2024_20260515")
CONFIG_SOURCE = "experiments/configs/nctrl_scaffolding.py"
RUN_ID = "run_nctrl_scaffolding_20260515"

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
    benchmark=SmallCapBenchmarkConfig(holding_period_bars=5, random_seed=42),
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
    "purpose": "nctrl_scaffolding_check",
    "research_item": "RESEARCH-046",
    "config_source": CONFIG_SOURCE,
    "baseline_symbols": list(BASELINE_SYMBOLS),
    "success_outcome": "end_to_end_artifact_generation_without_exceptions",
    "not_a_trial": True,
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


def run_scaffolding_check() -> dict[str, Any]:
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    static_metadata = build_static_metadata()
    static_metadata.to_csv(output_dir / "static_metadata.csv", index=False)

    raw_frames = {symbol: download_ticker(symbol, DOWNLOAD_START, REPORT_END) for symbol in BASELINE_SYMBOLS}
    iwm_frame = download_ticker(IWM_SYMBOL, DOWNLOAD_START, REPORT_END)
    vix_frame = download_ticker(VIX_SYMBOL, DOWNLOAD_START, REPORT_END)
    prepared_data = prepare_small_cap_historical_data(
        raw_frames,
        iwm_frame=iwm_frame,
        static_metadata=static_metadata,
        vix_frame=vix_frame,
    )
    result = run_small_cap_historical_report(
        prepared_data.candidate_metadata,
        prepared_data.frames,
        output_dir=output_dir,
        iwm_frame=prepared_data.iwm_frame,
        start=RUN_CONFIG.start,
        end=RUN_CONFIG.end,
        metadata_diagnostics=pd.DataFrame(),
        config=RUN_CONFIG,
        run_id=RUN_ID,
        trial_accounting=None,
        extras=EXTRAS,
    )
    _write_backtest_report_alias(result)
    _write_scaffolding_metrics(result, output_dir)
    return {"prepared_data": prepared_data, "run_result": result}


def _write_backtest_report_alias(result: dict[str, Any]) -> None:
    source = result["paths"]["backtest_report"]
    target = source.parent / "backtest_report.md"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _write_scaffolding_metrics(result: dict[str, Any], output_dir: Path) -> None:
    candidate_export = result["candidate_export"].copy()
    activity = _candidate_activity(candidate_export)
    rejections = _rejection_breakdown(candidate_export, result["portfolio_backtest"].rejections)
    summary = _summary(result, candidate_export, activity)
    activity.to_csv(output_dir / "scaffolding_candidate_activity.csv", index=False)
    rejections.to_csv(output_dir / "scaffolding_rejection_breakdown.csv", index=False)
    (output_dir / "scaffolding_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _candidate_activity(candidate_export: pd.DataFrame) -> pd.DataFrame:
    if candidate_export.empty:
        return pd.DataFrame(columns=["as_of", "rows", "operational_candidates", "has_operational_candidate"])
    grouped = candidate_export.assign(
        operational_flag=candidate_export["operational_candidate"].fillna(False).astype(bool)
    ).groupby("as_of", sort=True)
    return grouped.agg(
        rows=("symbol", "size"),
        operational_candidates=("operational_flag", "sum"),
    ).assign(
        has_operational_candidate=lambda data: data["operational_candidates"].gt(0)
    ).reset_index()


def _rejection_breakdown(candidate_export: pd.DataFrame, portfolio_rejections: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for layer, column in (
        ("universe", "universe_rejection_reasons"),
        ("scanner", "small_cap_scanner_reject_reason"),
        ("regime", "market_regime_block_reason"),
        ("execution_proxy", "small_cap_execution_skip_reason"),
    ):
        if column in candidate_export.columns:
            rows.extend(_count_reasons(layer, candidate_export[column]))
    if not portfolio_rejections.empty and "reject_reason" in portfolio_rejections.columns:
        rows.extend(_count_reasons("portfolio", portfolio_rejections["reject_reason"]))
    return pd.DataFrame(rows, columns=["layer", "reason", "count"]).sort_values(["layer", "count", "reason"], ascending=[True, False, True]).reset_index(drop=True)


def _count_reasons(layer: str, values: pd.Series) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for raw in values.fillna("").astype(str):
        for reason in [part.strip() for part in raw.split(";") if part.strip()]:
            counts[reason] = counts.get(reason, 0) + 1
    return [{"layer": layer, "reason": reason, "count": count} for reason, count in counts.items()]


def _summary(result: dict[str, Any], candidate_export: pd.DataFrame, activity: pd.DataFrame) -> dict[str, object]:
    required_artifacts = {
        "candidate_export": "candidate_export.csv",
        "run_manifest": "run_manifest.json",
        "portfolio_trade_log": "portfolio_trade_log.csv",
        "portfolio_equity_curve": "portfolio_equity_curve.csv",
        "portfolio_rejections": "portfolio_rejections.csv",
        "portfolio_summary": "portfolio_summary.csv",
        "backtest_report_alias": "backtest_report.md",
        "backtest_report": "small_cap_backtest_report.md",
    }
    artifact_status = {name: (OUTPUT_DIR / filename).exists() for name, filename in required_artifacts.items()}
    operational_total = int(candidate_export["operational_candidate"].fillna(False).astype(bool).sum()) if not candidate_export.empty else 0
    days = int(len(activity))
    days_with_candidate = int(activity["has_operational_candidate"].sum()) if not activity.empty else 0
    return {
        "purpose": EXTRAS["purpose"],
        "research_item": EXTRAS["research_item"],
        "config_source": CONFIG_SOURCE,
        "baseline_symbols": list(BASELINE_SYMBOLS),
        "download_start": DOWNLOAD_START,
        "report_start": REPORT_START,
        "report_end": REPORT_END,
        "artifact_status": artifact_status,
        "all_required_artifacts_present": all(artifact_status.values()),
        "candidate_rows": int(len(candidate_export)),
        "operational_candidates_total": operational_total,
        "candidate_days": days,
        "days_with_operational_candidate": days_with_candidate,
        "pct_days_with_operational_candidate": float(days_with_candidate / days) if days else 0.0,
        "avg_operational_candidates_per_day": float(activity["operational_candidates"].mean()) if not activity.empty else 0.0,
        "portfolio_total_trades": int(result["portfolio_backtest"].summary.get("total_trades", 0)),
        "trial_accounting_present": bool(result["run_manifest"].get("trial_accounting")),
        "manifest_purpose": result["run_manifest"].get("extras", {}).get("purpose"),
        "success_condition": "technical_pass_if_no_exception_and_required_artifacts_present",
    }


def main() -> int:
    result = run_scaffolding_check()
    summary_path = result["run_result"]["paths"]["run_manifest"].parent / "scaffolding_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
