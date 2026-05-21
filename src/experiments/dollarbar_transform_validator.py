from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.dollar_bar_diagnostic import (
    build_dollar_bars,
    diagnostic_verdict,
    distribution_stats,
    stability_score,
)


RUN_ID = "DOLLARBAR-TRANSFORM-VALIDATOR-001"
TRIAL_ID = "TRIAL-DOLLARBAR-TRANSFORM-001"
PREREG_DIR = Path("experiments/provider_aware_research/dollarbar_transform_preregistration_20260521")
ARTIFACT_DIR = Path("experiments/provider_aware_research/dollarbar_transform_validation_20260521")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-DollarBar-Transform-Validation-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-dollarbar-transform-validation.md")
EMA_SPAN = 20
FORBIDDEN_OUTPUT_COLUMNS = {
    "pnl",
    "win_rate",
    "signal_return",
    "trade_outcome",
    "sharpe",
    "profit_factor",
    "strategy_return",
}


def run_dollarbar_transform_validation(prereg_dir: str | Path = PREREG_DIR) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    prereg_path = Path(prereg_dir)
    input_panel = pd.read_csv(prereg_path / "input_panel.csv")
    diagnostics = []
    for _, row in input_panel.iterrows():
        diagnostics.append(validate_transform_file(str(row["panel_id"]), Path(str(row["bars_path"]))))
    _write_csv(ARTIFACT_DIR / "transform_validation_panel.csv", list(diagnostics[0].keys()), diagnostics)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    manifest = _write_manifest(diagnostics)
    decision = _write_decision(manifest, diagnostics)
    return decision


def validate_transform_file(panel_id: str, bars_path: Path) -> dict[str, Any]:
    frame = _load_bars(bars_path)
    static_target = float(frame["dollar_value"].sum()) / len(frame)
    static_bars = build_dollar_bars(frame, static_target)
    ema_bars = build_ema_dollar_bars(frame, span=EMA_SPAN)
    time_returns = _returns(frame["close"].astype(float).tolist())
    static_returns = _returns([row["close"] for row in static_bars])
    ema_returns = _returns([row["close"] for row in ema_bars])
    time_stats = distribution_stats(time_returns)
    static_stats = distribution_stats(static_returns)
    ema_stats = distribution_stats(ema_returns)
    static_score = stability_score(static_stats)
    ema_score = stability_score(ema_stats)
    stability_delta = ema_score - static_score
    sample_ratio = len(ema_bars) / len(frame) if len(frame) else 0.0
    verdict = transform_verdict(stability_delta, sample_ratio)
    return {
        "panel_id": panel_id,
        "symbol": str(frame["symbol"].iloc[0]),
        "bars_path": str(bars_path),
        "time_bar_count": len(frame),
        "static_bar_count": len(static_bars),
        "ema_bar_count": len(ema_bars),
        "ema_span": EMA_SPAN,
        "static_target_dollar_bucket": round(static_target, 6),
        "ema_median_target_dollar_bucket": round(median([row["target_dollar"] for row in ema_bars]), 6) if ema_bars else 0.0,
        "static_abs_skew": round(abs(static_stats["skew"]), 10),
        "ema_abs_skew": round(abs(ema_stats["skew"]), 10),
        "static_pearson_kurtosis": round(static_stats["pearson_kurtosis"], 10),
        "ema_pearson_kurtosis": round(ema_stats["pearson_kurtosis"], 10),
        "static_outlier_rate_3sigma": round(static_stats["outlier_rate_3sigma"], 10),
        "ema_outlier_rate_3sigma": round(ema_stats["outlier_rate_3sigma"], 10),
        "static_stability_score": round(static_score, 6),
        "ema_stability_score": round(ema_score, 6),
        "stability_score_delta": round(stability_delta, 6),
        "sample_ratio": round(sample_ratio, 6),
        "distribution_only_verdict": diagnostic_verdict(static_stats, ema_stats, len(ema_returns)),
        "transform_verdict": verdict,
    }


def build_ema_dollar_bars(frame: pd.DataFrame, span: int = EMA_SPAN) -> list[dict[str, Any]]:
    if span <= 1:
        raise ValueError("span must be greater than 1")
    working = frame.copy()
    working["target_dollar"] = working["dollar_value"].ewm(span=span, adjust=False).mean()
    fallback = float(working["dollar_value"].mean())
    bars: list[dict[str, Any]] = []
    bucket: list[pd.Series] = []
    bucket_dollars = 0.0
    current_target = fallback
    for _, row in working.iterrows():
        target = float(row["target_dollar"])
        if target <= 0:
            target = fallback
        if not bucket:
            current_target = target
        bucket.append(row)
        bucket_dollars += float(row["dollar_value"])
        if bucket_dollars >= current_target:
            collapsed = _collapse_ema_bucket(bucket, bucket_dollars, current_target)
            bars.append(collapsed)
            bucket = []
            bucket_dollars = 0.0
    if bucket:
        bars.append(_collapse_ema_bucket(bucket, bucket_dollars, current_target))
    return bars


def transform_verdict(stability_delta: float, sample_ratio: float) -> str:
    if sample_ratio < 0.20:
        return "FAIL_SAMPLE_GATE"
    if stability_delta > 0:
        return "PASS_DISTRIBUTION_STABILITY_GATE"
    return "FAIL_DISTRIBUTION_STABILITY_GATE"


def validate_dollarbar_transform_validation(validation_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(validation_dir)
    checks: list[dict[str, Any]] = []
    required_files = ["transform_validation_panel.csv", "blocked_actions.csv", "validation_manifest.json", "final_decision.json"]
    _check(checks, "validation_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required_files:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)

    panel = _read_csv(path / "transform_validation_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    manifest = json.loads((path / "validation_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(panel[0].keys()) if panel else set()
    forbidden_present = sorted(FORBIDDEN_OUTPUT_COLUMNS & columns)
    deltas = [float(row["stability_score_delta"]) for row in panel]
    sample_ratios = [float(row["sample_ratio"]) for row in panel]
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "forbidden_output_columns_absent", not forbidden_present, f"present={forbidden_present}")
    _check(checks, "ema_span_predeclared", all(int(row["ema_span"]) == EMA_SPAN for row in panel), f"span={EMA_SPAN}")
    _check(checks, "sample_gate_all_rows", all(value >= 0.20 for value in sample_ratios), f"sample_ratios={sample_ratios}")
    _check(checks, "median_delta_matches_decision", round(median(deltas), 6) == float(decision["median_stability_score_delta"]), f"deltas={deltas}")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked actions")
    _check(checks, "manifest_no_execution", manifest.get("backtest_performed") is False and manifest.get("provider_query_performed") is False, str(manifest))
    _check(checks, "decision_no_strategy", decision.get("decision") in {"DOLLARBAR_TRANSFORM_VALIDATED_FOR_DATA_LAYER_ONLY", "DOLLARBAR_TRANSFORM_REJECTED_FOR_DATA_LAYER"}, str(decision.get("decision")))
    _check(checks, "decision_no_trading", decision.get("paper_trading_performed") is False and decision.get("live_trading_performed") is False, str(decision))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate static vs EMA dollar-bar transform using distribution-only metrics.")
    parser.add_argument("--prereg-dir", default=str(PREREG_DIR))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_dollarbar_transform_validation(args.prereg_dir)
    report = validate_dollarbar_transform_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Validation uses frozen existing input panel."],
        ["strategy_backtest", "blocked", "Data transform validation is not a strategy test."],
        ["read_pnl", "blocked", "PnL metrics are forbidden by preregistration."],
        ["directional_signal_generation", "blocked", "No directional signal is part of this validator."],
        ["paper_trading", "blocked", "No strategy exists."],
        ["live_trading", "blocked", "No strategy exists."],
        ["strategy_promotion", "blocked", "A passing transform can only move to data-layer use."],
    ]


def _load_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame = frame[(frame["close"] > 0) & (frame["volume"] >= 0)].copy()
    frame["dollar_value"] = frame["close"].astype(float) * frame["volume"].astype(float)
    if len(frame) < 5 or float(frame["dollar_value"].sum()) <= 0:
        raise ValueError(f"insufficient bars for transform validation: {path}")
    return frame


def _collapse_ema_bucket(bucket: list[pd.Series], bucket_dollars: float, target_dollar: float) -> dict[str, Any]:
    return {
        "timestamp": bucket[-1]["timestamp"],
        "open": float(bucket[0]["open"]),
        "high": max(float(row["high"]) for row in bucket),
        "low": min(float(row["low"]) for row in bucket),
        "close": float(bucket[-1]["close"]),
        "volume": sum(float(row["volume"]) for row in bucket),
        "dollar_value": bucket_dollars,
        "target_dollar": target_dollar,
    }


def _returns(closes: list[float]) -> list[float]:
    values: list[float] = []
    for previous, current in zip(closes, closes[1:]):
        if previous > 0:
            values.append((current / previous) - 1.0)
    return values


def _write_manifest(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    pass_count = sum(1 for row in diagnostics if row["transform_verdict"] == "PASS_DISTRIBUTION_STABILITY_GATE")
    deltas = [float(row["stability_score_delta"]) for row in diagnostics]
    median_delta = median(deltas) if deltas else 0.0
    decision = (
        "DOLLARBAR_TRANSFORM_VALIDATED_FOR_DATA_LAYER_ONLY"
        if pass_count / len(diagnostics) >= 0.80 and median_delta > 0
        else "DOLLARBAR_TRANSFORM_REJECTED_FOR_DATA_LAYER"
    )
    manifest = {
        "status": "validation_complete_not_strategy",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "ema_span": EMA_SPAN,
        "evaluated_file_count": len(diagnostics),
        "pass_distribution_stability_count": pass_count,
        "coverage_rate": round(pass_count / len(diagnostics), 6) if diagnostics else 0.0,
        "median_stability_score_delta": round(median_delta, 6),
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(ARTIFACT_DIR / "validation_manifest.json", manifest)
    return manifest


def _write_decision(manifest: dict[str, Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    decision = {
        "status": "validation_complete_not_strategy",
        "decision": manifest["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "ema_span": EMA_SPAN,
        "evaluated_file_count": manifest["evaluated_file_count"],
        "pass_distribution_stability_count": manifest["pass_distribution_stability_count"],
        "coverage_rate": manifest["coverage_rate"],
        "median_stability_score_delta": manifest["median_stability_score_delta"],
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If validated, allow EMA dollar-bar transform as a data-layer candidate in future preregistered strategy specs only.",
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
        f"- {row['panel_id']} {row['symbol']} delta={row['stability_score_delta']} sample_ratio={row['sample_ratio']} verdict={row['transform_verdict']}"
        for row in diagnostics
    )
    return (
        "# Report DollarBar Transform Validation - 2026-05-21\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Distribution-only validation of static average-dollar bars versus rolling EMA dollar bars. "
        "No PnL, win rate, signal return, strategy return, provider query, backtest, paper/live trading or promotion was used.\n\n"
        "## Result\n\n"
        f"- Evaluated files: {decision['evaluated_file_count']}\n"
        f"- EMA span: {decision['ema_span']}\n"
        f"- Coverage rate: {decision['coverage_rate']}\n"
        f"- Median stability score delta: {decision['median_stability_score_delta']}\n\n"
        "## Panel\n\n"
        f"{rows}\n"
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
        "gate_decision": "DOLLARBAR_TRANSFORM_VALIDATION_PASS" if failed == 0 else "DOLLARBAR_TRANSFORM_VALIDATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
