from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd


PRIMARY_BENCHMARK = "equal_weight_universe"
STRATEGY_PROXY_BENCHMARK = "ticker_holding_window"


def build_small_cap_backtest_report(
    candidate_export: pd.DataFrame,
    benchmark_report: pd.DataFrame,
    primary_benchmark: str = PRIMARY_BENCHMARK,
    metadata_diagnostics: pd.DataFrame | None = None,
    portfolio_summary: dict[str, Any] | None = None,
    portfolio_rejection_summary: dict[str, int] | None = None,
    portfolio_outlier_breakdown: dict[str, Any] | None = None,
    portfolio_score_profile: pd.DataFrame | None = None,
    run_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    strategy_return = _benchmark_return(benchmark_report, STRATEGY_PROXY_BENCHMARK)
    primary_return = _benchmark_return(benchmark_report, primary_benchmark)
    excess_return = _excess_return(strategy_return, primary_return)
    verdict = _verdict(excess_return)
    return {
        "verdict": verdict,
        "candidate_summary": _candidate_summary(candidate_export),
        "primary_benchmark": primary_benchmark,
        "strategy_proxy_return": strategy_return,
        "primary_benchmark_return": primary_return,
        "excess_return": excess_return,
        "benchmark_report": _records(benchmark_report),
        "setup_counts": _counts(candidate_export, "small_cap_setup", operational_only=True),
        "regime_block_reasons": _reason_counts(candidate_export, "market_regime_block_reason"),
        "execution_skip_reasons": _reason_counts(candidate_export, "small_cap_execution_skip_reason"),
        "universe_rejection_reasons": _reason_counts(candidate_export, "universe_rejection_reasons"),
        "scanner_reject_reasons": _reason_counts(candidate_export, "small_cap_scanner_reject_reason"),
        "metadata_diagnostics": _records(metadata_diagnostics) if metadata_diagnostics is not None else [],
        "metadata_diagnostic_reasons": _metadata_diagnostic_reasons(metadata_diagnostics),
        "portfolio_summary": portfolio_summary or {},
        "portfolio_return": _portfolio_return(portfolio_summary),
        "portfolio_rejection_summary": portfolio_rejection_summary or {},
        "portfolio_outlier_breakdown": portfolio_outlier_breakdown or {},
        "portfolio_score_profile": _records(portfolio_score_profile) if portfolio_score_profile is not None else [],
        "run_manifest": run_manifest or {},
        "decision": _decision(verdict),
    }


def write_small_cap_backtest_report_markdown(
    candidate_export: pd.DataFrame,
    benchmark_report: pd.DataFrame,
    output_path: Path,
    primary_benchmark: str = PRIMARY_BENCHMARK,
    metadata_diagnostics: pd.DataFrame | None = None,
    portfolio_summary: dict[str, Any] | None = None,
    portfolio_rejection_summary: dict[str, int] | None = None,
    portfolio_outlier_breakdown: dict[str, Any] | None = None,
    portfolio_score_profile: pd.DataFrame | None = None,
    run_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_small_cap_backtest_report(
        candidate_export,
        benchmark_report,
        primary_benchmark=primary_benchmark,
        metadata_diagnostics=metadata_diagnostics,
        portfolio_summary=portfolio_summary,
        portfolio_rejection_summary=portfolio_rejection_summary,
        portfolio_outlier_breakdown=portfolio_outlier_breakdown,
        portfolio_score_profile=portfolio_score_profile,
        run_manifest=run_manifest,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_to_markdown(report), encoding="utf-8")
    return report


def _candidate_summary(candidate_export: pd.DataFrame) -> dict[str, Any]:
    if candidate_export.empty:
        return {
            "rows": 0,
            "operational_candidates": 0,
            "unique_symbols": 0,
            "candidate_dates": 0,
            "conversion_rate": 0.0,
            "total_position_notional": 0.0,
            "operational_position_notional": 0.0,
        }
    rows = int(len(candidate_export))
    operational = _operational_mask(candidate_export)
    operational_count = int(operational.sum())
    return {
        "rows": rows,
        "operational_candidates": operational_count,
        "unique_symbols": int(candidate_export["symbol"].nunique()) if "symbol" in candidate_export.columns else 0,
        "candidate_dates": _candidate_date_count(candidate_export),
        "conversion_rate": float(operational_count / rows) if rows else 0.0,
        "total_position_notional": _numeric_sum(candidate_export, "small_cap_position_notional"),
        "operational_position_notional": _numeric_sum(candidate_export[operational].copy(), "small_cap_position_notional"),
    }


def _candidate_date_count(candidate_export: pd.DataFrame) -> int:
    if "as_of" not in candidate_export.columns:
        return 0
    dates = pd.to_datetime(candidate_export["as_of"], errors="coerce").dropna()
    return int(dates.dt.normalize().nunique())


def _operational_mask(candidate_export: pd.DataFrame) -> pd.Series:
    if "operational_candidate" not in candidate_export.columns:
        return pd.Series(False, index=candidate_export.index)
    return candidate_export["operational_candidate"].fillna(False).astype(bool)


def _numeric_sum(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).sum())


def _benchmark_return(benchmark_report: pd.DataFrame, benchmark: str) -> float:
    if benchmark_report.empty or "benchmark" not in benchmark_report.columns or "return" not in benchmark_report.columns:
        return float("nan")
    rows = benchmark_report[benchmark_report["benchmark"] == benchmark]
    if rows.empty:
        return float("nan")
    return _safe_float(rows.iloc[0]["return"])


def _excess_return(strategy_return: float, primary_return: float) -> float:
    if math.isnan(strategy_return) or math.isnan(primary_return):
        return float("nan")
    return float(strategy_return - primary_return)


def _verdict(excess_return: float) -> str:
    if math.isnan(excess_return):
        return "insufficient_data"
    if excess_return > 0:
        return "beats_primary_benchmark"
    return "underperforming_primary_benchmark"


def _decision(verdict: str) -> str:
    if verdict == "beats_primary_benchmark":
        return "Candidata a ulteriore validazione: il proxy holding-window batte il benchmark primario nel report corrente."
    if verdict == "underperforming_primary_benchmark":
        return "Non promuovere la strategia: resta sotto il benchmark primario nel report corrente."
    return "Non promuovere la strategia: dati insufficienti per valutare il report small-cap."


def _counts(candidate_export: pd.DataFrame, column: str, operational_only: bool = False) -> dict[str, int]:
    if candidate_export.empty or column not in candidate_export.columns:
        return {}
    data = candidate_export.copy()
    if operational_only:
        data = data[_operational_mask(data)]
    values = data[column].fillna("").astype(str)
    values = values[values != ""]
    return {str(key): int(value) for key, value in values.value_counts().sort_index().items()}


def _reason_counts(candidate_export: pd.DataFrame, column: str) -> dict[str, int]:
    if candidate_export.empty or column not in candidate_export.columns:
        return {}
    counts: dict[str, int] = {}
    for raw in candidate_export[column].fillna("").astype(str):
        for reason in raw.split(";"):
            reason = reason.strip()
            if reason:
                counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _metadata_diagnostic_reasons(metadata_diagnostics: pd.DataFrame | None) -> dict[str, int]:
    if metadata_diagnostics is None or metadata_diagnostics.empty or "reason" not in metadata_diagnostics.columns:
        return {}
    counts: dict[str, int] = {}
    for reason in metadata_diagnostics["reason"].fillna("").astype(str):
        reason = reason.strip()
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _portfolio_return(portfolio_summary: dict[str, Any] | None) -> float:
    if not portfolio_summary:
        return float("nan")
    return _safe_float(portfolio_summary.get("return_pct"))


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for record in frame.to_dict(orient="records"):
        records.append({key: _json_safe(value) for key, value in record.items()})
    return records


def _to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Small-Cap Backtest Report",
        "",
    ]
    manifest_lines = _manifest_lines(report.get("run_manifest"))
    if manifest_lines:
        lines.extend(manifest_lines)
        lines.append("")
    lines.extend(
        [
            f"Verdict: `{report['verdict']}`",
            "",
            f"Decision: {report['decision']}",
            "",
            "## Candidate Summary",
        ]
    )
    for key, value in report["candidate_summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Benchmark Comparison",
            f"- strategy_proxy_return: {report['strategy_proxy_return']}",
            f"- primary_benchmark: {report['primary_benchmark']}",
            f"- primary_benchmark_return: {report['primary_benchmark_return']}",
            f"- excess_return: {report['excess_return']}",
            "",
            "## Setup Counts",
        ]
    )
    lines.extend(_dict_lines(report["setup_counts"]))
    lines.extend(["", "## Universe Rejection Reasons"])
    lines.extend(_dict_lines(report["universe_rejection_reasons"]))
    lines.extend(["", "## Scanner Reject Reasons"])
    lines.extend(_dict_lines(report["scanner_reject_reasons"]))
    lines.extend(["", "## Regime Block Reasons"])
    lines.extend(_dict_lines(report["regime_block_reasons"]))
    lines.extend(["", "## Execution Skip Reasons"])
    lines.extend(_dict_lines(report["execution_skip_reasons"]))
    lines.extend(["", "## Metadata Diagnostics"])
    lines.extend(_dict_lines(report["metadata_diagnostic_reasons"]))
    for row in report["metadata_diagnostics"]:
        lines.append(f"- {row.get('symbol')}: status={row.get('status')}, reason={row.get('reason')}")
    lines.extend(["", "## Portfolio Backtest"])
    lines.extend(_value_lines(report["portfolio_summary"]))
    lines.extend(["", "## Portfolio Rejection Summary"])
    lines.extend(_dict_lines(report["portfolio_rejection_summary"]))
    lines.extend(["", "## Portfolio Outlier Breakdown"])
    lines.extend(_value_lines(report["portfolio_outlier_breakdown"]))
    lines.extend(["", "## Score Profile Report"])
    lines.extend(_record_lines(report["portfolio_score_profile"]))
    lines.extend(["", "## Benchmarks"])
    for row in report["benchmark_report"]:
        lines.append(f"- {row.get('benchmark')}: return={row.get('return')}, observations={row.get('observations')}")
    lines.append("")
    return "\n".join(lines)


def _manifest_lines(manifest: dict[str, Any] | None) -> list[str]:
    if not manifest:
        return []
    period = manifest.get("period") or {}
    universe = manifest.get("universe") or []
    if isinstance(universe, (list, tuple)):
        universe_repr = ", ".join(str(item) for item in universe) if universe else "n/a"
    else:
        universe_repr = str(universe)
    lines = ["## Run Manifest"]
    lines.append(f"- run_id: {manifest.get('run_id', 'n/a')}")
    lines.append(f"- config_hash: {manifest.get('config_hash', 'n/a')}")
    lines.append(f"- schema_version: {manifest.get('schema_version', 'n/a')}")
    lines.append(f"- created_at: {manifest.get('created_at', 'n/a')}")
    lines.append(f"- period_start: {period.get('start', 'n/a')}")
    lines.append(f"- period_end: {period.get('end', 'n/a')}")
    lines.append(f"- universe: {universe_repr}")
    git_commit = manifest.get("git_commit")
    lines.append(f"- git_commit: {git_commit if git_commit else 'n/a'}")
    host = manifest.get("host")
    lines.append(f"- host: {host if host else 'n/a'}")
    return lines


def _dict_lines(values: dict[str, int]) -> list[str]:
    if not values:
        return ["- none: 0"]
    return [f"- {key}: {value}" for key, value in values.items()]


def _value_lines(values: dict[str, Any]) -> list[str]:
    if not values:
        return ["- none: 0"]
    return [f"- {key}: {value}" for key, value in values.items()]


def _record_lines(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return ["- none: 0"]
    return ["- " + ", ".join(f"{key}={value}" for key, value in row.items()) for row in records]


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed


def _json_safe(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
