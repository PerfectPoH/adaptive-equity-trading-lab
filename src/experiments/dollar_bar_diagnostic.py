from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import pandas as pd


RUN_ID = "DOLLAR-BAR-DIAGNOSTIC-001"
TRIAL_ID = "TRIAL-DOLLARBAR-DIAGNOSTIC-001"
ARTIFACT_DIR = Path("experiments/provider_aware_research/dollar_bar_diagnostic_20260521")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Dollar-Bar-Diagnostic-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-dollar-bar-diagnostic.md")
DEFAULT_BARS_ROOT = Path("experiments/provider_aware_research/data_inputs/gaprev_mini_panel_databento_intraday_probe_20260521")


def run_dollar_bar_diagnostic(bars_root: str | Path = DEFAULT_BARS_ROOT) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    bar_files = sorted(Path(bars_root).glob("*/bars.csv"))
    diagnostics = [diagnose_bars_file(path) for path in bar_files]
    diagnostics = [row for row in diagnostics if row["status"] == "evaluated"]
    _write_csv(ARTIFACT_DIR / "dollar_bar_diagnostic_panel.csv", list(diagnostics[0].keys()), diagnostics)
    _write_csv(
        ARTIFACT_DIR / "input_bars_panel.csv",
        ["bars_path"],
        [[str(path)] for path in bar_files],
    )
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    manifest = _write_manifest(diagnostics, bar_files)
    decision = _write_decision(manifest, diagnostics)
    return decision


def diagnose_bars_file(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path)
    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
    missing = sorted(required - set(frame.columns))
    if missing:
        return {"status": "missing_columns", "bars_path": str(path), "missing_columns": ";".join(missing)}
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame = frame[(frame["close"] > 0) & (frame["volume"] >= 0)].copy()
    frame["dollar_value"] = frame["close"].astype(float) * frame["volume"].astype(float)
    if len(frame) < 5 or float(frame["dollar_value"].sum()) <= 0:
        return {"status": "insufficient_data", "bars_path": str(path)}
    target_dollar = float(frame["dollar_value"].sum()) / len(frame)
    dollar_bars = build_dollar_bars(frame, target_dollar)
    time_returns = _returns(frame["close"].astype(float).tolist())
    dollar_returns = _returns([row["close"] for row in dollar_bars])
    time_stats = distribution_stats(time_returns)
    dollar_stats = distribution_stats(dollar_returns)
    verdict = diagnostic_verdict(time_stats, dollar_stats, len(dollar_returns))
    return {
        "status": "evaluated",
        "symbol": str(frame["symbol"].iloc[0]),
        "bars_path": str(path),
        "time_bar_count": len(frame),
        "dollar_bar_count": len(dollar_bars),
        "target_dollar_bucket": round(target_dollar, 6),
        "time_return_std": round(time_stats["std"], 10),
        "dollar_return_std": round(dollar_stats["std"], 10),
        "time_abs_skew": round(abs(time_stats["skew"]), 10),
        "dollar_abs_skew": round(abs(dollar_stats["skew"]), 10),
        "time_pearson_kurtosis": round(time_stats["pearson_kurtosis"], 10),
        "dollar_pearson_kurtosis": round(dollar_stats["pearson_kurtosis"], 10),
        "time_outlier_rate_3sigma": round(time_stats["outlier_rate_3sigma"], 10),
        "dollar_outlier_rate_3sigma": round(dollar_stats["outlier_rate_3sigma"], 10),
        "stability_score_delta": round(stability_score(dollar_stats) - stability_score(time_stats), 6),
        "diagnostic_verdict": verdict,
    }


def build_dollar_bars(frame: pd.DataFrame, target_dollar: float) -> list[dict[str, Any]]:
    if target_dollar <= 0:
        raise ValueError("target_dollar must be positive")
    bars: list[dict[str, Any]] = []
    bucket: list[pd.Series] = []
    bucket_dollars = 0.0
    for _, row in frame.iterrows():
        bucket.append(row)
        bucket_dollars += float(row["dollar_value"])
        if bucket_dollars >= target_dollar:
            bars.append(_collapse_bucket(bucket, bucket_dollars))
            bucket = []
            bucket_dollars = 0.0
    if bucket:
        bars.append(_collapse_bucket(bucket, bucket_dollars))
    return bars


def distribution_stats(values: list[float]) -> dict[str, float]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if len(clean) < 2:
        return {"std": 0.0, "skew": 0.0, "pearson_kurtosis": 0.0, "outlier_rate_3sigma": 0.0}
    mu = mean(clean)
    sigma = pstdev(clean)
    if sigma == 0:
        return {"std": 0.0, "skew": 0.0, "pearson_kurtosis": 0.0, "outlier_rate_3sigma": 0.0}
    z = [(value - mu) / sigma for value in clean]
    skew = mean([value**3 for value in z])
    kurtosis = mean([value**4 for value in z])
    outlier_rate = sum(1 for value in z if abs(value) > 3) / len(z)
    return {"std": sigma, "skew": skew, "pearson_kurtosis": kurtosis, "outlier_rate_3sigma": outlier_rate}


def stability_score(stats: dict[str, float]) -> float:
    return -abs(stats["skew"]) - max(0.0, stats["pearson_kurtosis"] - 3.0) - 10.0 * stats["outlier_rate_3sigma"]


def diagnostic_verdict(time_stats: dict[str, float], dollar_stats: dict[str, float], dollar_return_count: int) -> str:
    if dollar_return_count < 5:
        return "INSUFFICIENT_DOLLAR_BARS"
    improved = stability_score(dollar_stats) > stability_score(time_stats)
    if improved:
        return "DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY"
    return "DOLLAR_BARS_NO_STABILITY_IMPROVEMENT"


def validate_dollar_bar_diagnostic(diag_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(diag_dir)
    checks: list[dict[str, Any]] = []
    required_files = ["dollar_bar_diagnostic_panel.csv", "input_bars_panel.csv", "blocked_actions.csv", "diagnostic_manifest.json", "final_decision.json"]
    _check(checks, "diagnostic_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required_files:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)
    panel = _read_csv(path / "dollar_bar_diagnostic_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    manifest = json.loads((path / "diagnostic_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    required_columns = {
        "symbol",
        "time_bar_count",
        "dollar_bar_count",
        "target_dollar_bucket",
        "stability_score_delta",
        "diagnostic_verdict",
    }
    columns = set(panel[0].keys()) if panel else set()
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "required_columns_present", required_columns.issubset(columns), f"missing={sorted(required_columns - columns)}")
    _check(checks, "all_rows_evaluated", all(row["status"] == "evaluated" for row in panel), "evaluated rows")
    _check(checks, "bucket_positive", all(float(row["target_dollar_bucket"]) > 0 for row in panel), "positive buckets")
    _check(checks, "no_strategy_verdicts", all("PROMOTION" not in row["diagnostic_verdict"] and "TRADE" not in row["diagnostic_verdict"] for row in panel), "diagnostic only")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked actions")
    _check(checks, "manifest_no_execution", manifest.get("backtest_performed") is False and manifest.get("provider_query_performed") is False, str(manifest))
    _check(checks, "decision_no_execution", decision.get("decision") == "DOLLAR_BAR_DIAGNOSTIC_COMPLETE_NO_STRATEGY", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run dollar-bar diagnostics on existing intraday bars.")
    parser.add_argument("--bars-root", default=str(DEFAULT_BARS_ROOT))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_dollar_bar_diagnostic(args.bars_root)
    report = validate_dollar_bar_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Diagnostic uses already stored intraday bars."],
        ["run_strategy_backtest", "blocked", "Dollar bars are a representation diagnostic, not an entry rule."],
        ["select_bucket_from_pnl", "blocked", "Bucket size is fixed by average dollar flow, not optimized for returns."],
        ["paper_trading", "blocked", "No strategy signal exists."],
        ["live_trading", "blocked", "No strategy signal exists."],
    ]


def _collapse_bucket(bucket: list[pd.Series], bucket_dollars: float) -> dict[str, Any]:
    return {
        "timestamp": bucket[-1]["timestamp"],
        "open": float(bucket[0]["open"]),
        "high": max(float(row["high"]) for row in bucket),
        "low": min(float(row["low"]) for row in bucket),
        "close": float(bucket[-1]["close"]),
        "volume": sum(float(row["volume"]) for row in bucket),
        "dollar_value": bucket_dollars,
    }


def _returns(closes: list[float]) -> list[float]:
    values: list[float] = []
    for previous, current in zip(closes, closes[1:]):
        if previous > 0:
            values.append((current / previous) - 1.0)
    return values


def _write_manifest(diagnostics: list[dict[str, Any]], bar_files: list[Path]) -> dict[str, Any]:
    improved = sum(1 for row in diagnostics if row["diagnostic_verdict"] == "DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY")
    manifest = {
        "status": "diagnostic_complete_not_executable",
        "decision": "DOLLAR_BAR_DIAGNOSTIC_COMPLETE_NO_STRATEGY",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "input_file_count": len(bar_files),
        "evaluated_file_count": len(diagnostics),
        "improved_distribution_count": improved,
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(ARTIFACT_DIR / "diagnostic_manifest.json", manifest)
    return manifest


def _write_decision(manifest: dict[str, Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    deltas = [float(row["stability_score_delta"]) for row in diagnostics]
    median_delta = median(deltas) if deltas else 0.0
    decision = {
        "status": "diagnostic_complete_not_executable",
        "decision": "DOLLAR_BAR_DIAGNOSTIC_COMPLETE_NO_STRATEGY",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "evaluated_file_count": manifest["evaluated_file_count"],
        "improved_distribution_count": manifest["improved_distribution_count"],
        "median_stability_score_delta": round(median_delta, 6),
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If distribution stability improves broadly, preregister a separate data-transform validator before any strategy test.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, diagnostics)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], diagnostics: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"- {row['symbol']} bars={row['time_bar_count']} dollar_bars={row['dollar_bar_count']} "
        f"delta={row['stability_score_delta']} verdict={row['diagnostic_verdict']}"
        for row in diagnostics
    )
    return (
        "# Report Dollar-Bar Diagnostic - 2026-05-21\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Diagnostic-only transformation of existing Databento intraday bar artifacts into dollar bars. "
        "No provider query, strategy backtest, paper/live trading or promotion was performed.\n\n"
        "## Result\n\n"
        f"- Evaluated files: {decision['evaluated_file_count']}\n"
        f"- Improved distributions: {decision['improved_distribution_count']}\n"
        f"- Median stability score delta: {decision['median_stability_score_delta']}\n\n"
        "## Panel\n\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "Dollar bars are only a data representation candidate. A positive diagnostic does not imply alpha; "
        "it only justifies a future preregistered data-transform validator.\n"
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]] | list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if rows and isinstance(rows[0], dict):
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)  # type: ignore[arg-type]
        else:
            writer = csv.writer(handle)
            writer.writerow(fieldnames)
            writer.writerows(rows)  # type: ignore[arg-type]


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "DOLLAR_BAR_DIAGNOSTIC_PASS" if failed == 0 else "DOLLAR_BAR_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
