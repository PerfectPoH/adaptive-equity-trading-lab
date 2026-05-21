from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


SPEC_DIR = Path("experiments/provider_aware_research/dollarbar_transform_preregistration_20260521")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-DollarBar-Transform-Preregistration-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-dollarbar-transform-preregistration.md")

REQUIRED_FILES = [
    "README.md",
    "transform_manifest.json",
    "input_panel.csv",
    "transform_candidates.csv",
    "allowed_metrics.csv",
    "forbidden_metrics.csv",
    "decision_rule.csv",
    "blocked_actions.csv",
]

REQUIRED_ALLOWED_METRICS = {
    "absolute_skew",
    "pearson_kurtosis",
    "outlier_rate_3sigma",
    "bar_count_stability",
    "median_stability_score_delta",
    "coverage_rate",
}

REQUIRED_FORBIDDEN_METRICS = {
    "pnl",
    "win_rate",
    "signal_return",
    "trade_outcome",
    "sharpe",
    "profit_factor",
    "strategy_return",
}

REQUIRED_TRANSFORMS = {
    "static_average_dollar_bucket",
    "rolling_ema_dollar_bucket",
}

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "strategy_backtest",
    "bucket_selection_from_pnl",
    "directional_signal_generation",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def create_dollarbar_transform_preregistration(spec_dir: str | Path = SPEC_DIR) -> dict[str, Any]:
    path = Path(spec_dir)
    path.mkdir(parents=True, exist_ok=True)
    input_rows = _input_panel_rows()
    _write_text(path / "README.md", _readme())
    _write_json(path / "transform_manifest.json", _manifest(input_rows))
    _write_csv(path / "input_panel.csv", ["panel_id", "bars_path", "status"], input_rows)
    _write_csv(
        path / "transform_candidates.csv",
        ["transform_id", "status", "bucket_rule", "parameter_policy", "notes"],
        [
            [
                "static_average_dollar_bucket",
                "baseline",
                "target_dollar_bucket = total_dollar_volume / time_bar_count",
                "fixed_not_optimized",
                "Current diagnostic baseline; uses no return or PnL information.",
            ],
            [
                "rolling_ema_dollar_bucket",
                "candidate",
                "target_dollar_bucket_t = EMA(dollar_value, span=predeclared_window)",
                "window_predeclared_distribution_only",
                "Adaptive representation candidate; evaluated only on distribution stability metrics.",
            ],
        ],
    )
    _write_csv(
        path / "allowed_metrics.csv",
        ["metric", "status", "reason"],
        [
            ["absolute_skew", "allowed", "Measures asymmetry of representation returns."],
            ["pearson_kurtosis", "allowed", "Measures tail thickness using Pearson convention."],
            ["outlier_rate_3sigma", "allowed", "Measures extreme standardized returns."],
            ["bar_count_stability", "allowed", "Guards against transforms that collapse sample size."],
            ["median_stability_score_delta", "allowed", "Primary distribution-only comparison metric."],
            ["coverage_rate", "allowed", "Ensures transform works across the frozen panel."],
        ],
    )
    _write_csv(
        path / "forbidden_metrics.csv",
        ["metric", "status", "reason"],
        [
            ["pnl", "forbidden", "Would turn representation selection into strategy optimization."],
            ["win_rate", "forbidden", "Depends on trade outcomes."],
            ["signal_return", "forbidden", "Requires directional signal evaluation."],
            ["trade_outcome", "forbidden", "Leaks strategy behavior into data-transform choice."],
            ["sharpe", "forbidden", "Performance metric, not representation metric."],
            ["profit_factor", "forbidden", "Performance metric, not representation metric."],
            ["strategy_return", "forbidden", "Directly optimizes the future strategy layer."],
        ],
    )
    _write_csv(
        path / "decision_rule.csv",
        ["decision_item", "status", "rule"],
        [
            ["execution_status", "blocked", "Spec is preregistration only."],
            ["primary_metric", "required", "median_stability_score_delta > 0 on frozen panel."],
            ["coverage_gate", "required", "coverage_rate >= 0.80."],
            ["sample_gate", "required", "transformed bar count must remain >= 20% of time-bar count per file."],
            ["profit_metric_gate", "blocked", "No PnL or trade outcome metric may appear in selection."],
            ["promotion_rule", "blocked", "A passing transform can only move to data-transform validator, not strategy execution."],
        ],
    )
    _write_csv(
        path / "blocked_actions.csv",
        ["action", "status", "reason"],
        [[action, "blocked", "Not authorized by transform preregistration."] for action in sorted(REQUIRED_BLOCKED_ACTIONS)],
    )
    report = validate_dollarbar_transform_preregistration(path)
    _write_report(report)
    return report


def validate_dollarbar_transform_preregistration(spec_dir: str | Path = SPEC_DIR) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, Any]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "transform_manifest.json").read_text(encoding="utf-8"))
    input_panel = pd.read_csv(path / "input_panel.csv")
    transforms = pd.read_csv(path / "transform_candidates.csv")
    allowed = pd.read_csv(path / "allowed_metrics.csv")
    forbidden = pd.read_csv(path / "forbidden_metrics.csv")
    decision = pd.read_csv(path / "decision_rule.csv")
    blocked = pd.read_csv(path / "blocked_actions.csv")

    _check(checks, "manifest_spec_only", manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "manifest_no_execution", _all_false(manifest, ["provider_query_performed", "backtest_performed", "paper_trading_performed", "live_trading_performed", "strategy_promotion_performed"]), str(manifest))
    _check(checks, "input_panel_minimum_12", len(input_panel) >= 12, f"rows={len(input_panel)}")
    _check(checks, "input_panel_existing_paths", input_panel["bars_path"].map(lambda value: Path(str(value)).is_file()).all(), "all paths exist")
    transform_ids = set(transforms["transform_id"].astype(str))
    _check(checks, "required_transforms_present", REQUIRED_TRANSFORMS.issubset(transform_ids), f"missing={sorted(REQUIRED_TRANSFORMS - transform_ids)}")
    _check(checks, "transform_parameters_not_pnl_optimized", not transforms["parameter_policy"].astype(str).str.lower().str.contains("pnl|return|profit").any(), "no pnl optimization")
    allowed_metrics = set(allowed["metric"].astype(str))
    forbidden_metrics = set(forbidden["metric"].astype(str))
    _check(checks, "allowed_metrics_required_set", REQUIRED_ALLOWED_METRICS.issubset(allowed_metrics), f"missing={sorted(REQUIRED_ALLOWED_METRICS - allowed_metrics)}")
    _check(checks, "forbidden_metrics_required_set", REQUIRED_FORBIDDEN_METRICS.issubset(forbidden_metrics), f"missing={sorted(REQUIRED_FORBIDDEN_METRICS - forbidden_metrics)}")
    _check(checks, "allowed_forbidden_disjoint", allowed_metrics.isdisjoint(forbidden_metrics), f"overlap={sorted(allowed_metrics & forbidden_metrics)}")
    _check(checks, "forbidden_metrics_all_forbidden", forbidden["status"].astype(str).str.lower().eq("forbidden").all(), "forbidden statuses")
    decision_rows = {str(row["decision_item"]): str(row["status"]).lower() for _, row in decision.iterrows()}
    _check(checks, "decision_execution_blocked", decision_rows.get("execution_status") == "blocked", str(decision_rows.get("execution_status")))
    _check(checks, "decision_profit_gate_blocked", decision_rows.get("profit_metric_gate") == "blocked", str(decision_rows.get("profit_metric_gate")))
    _check(checks, "decision_promotion_blocked", decision_rows.get("promotion_rule") == "blocked", str(decision_rows.get("promotion_rule")))
    blocked_actions = set(blocked["action"].astype(str))
    _check(checks, "blocked_actions_required_set", REQUIRED_BLOCKED_ACTIONS.issubset(blocked_actions), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked_actions)}")
    _check(checks, "blocked_actions_all_blocked", blocked["status"].astype(str).str.lower().eq("blocked").all(), "blocked statuses")
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate dollar-bar transform preregistration.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_only:
        report = validate_dollarbar_transform_preregistration(args.spec_dir)
    else:
        report = create_dollarbar_transform_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _input_panel_rows() -> list[list[str]]:
    paths = sorted(Path("experiments/provider_aware_research/data_inputs/gaprev_mini_panel_databento_intraday_probe_20260521").glob("*/bars.csv"))
    return [[f"DBAR-{index:03d}", str(path), "frozen_existing_artifact"] for index, path in enumerate(paths, start=1)]


def _manifest(input_rows: list[list[str]]) -> dict[str, Any]:
    return {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "DOLLARBAR_TRANSFORM_PREREGISTERED_NOT_EXECUTED",
        "trial_id": "TRIAL-DOLLARBAR-TRANSFORM-001",
        "preregistration_id": "PREREG-DOLLARBAR-TRANSFORM-001",
        "input_panel_count": len(input_rows),
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def _readme() -> str:
    return (
        "# PREREG-DOLLARBAR-TRANSFORM-001\n\n"
        "Status: `SPEC_ONLY_NOT_EXECUTED`.\n\n"
        "This preregistration defines a data-transform validation gate for dollar bars. "
        "It compares static average-dollar buckets against a rolling EMA dollar-bucket candidate using distribution-only metrics. "
        "No PnL, win rate, signal return, Sharpe, profit factor, trade outcome, strategy execution, paper trading or live trading is authorized.\n"
    )


def _write_report(report: dict[str, Any]) -> None:
    text = (
        "# Report DollarBar Transform Preregistration - 2026-05-21\n\n"
        f"Decision: `{report['gate_decision']}`\n\n"
        "Created `PREREG-DOLLARBAR-TRANSFORM-001` as a spec-only data-transform gate. "
        "The transform may only be evaluated on distribution stability metrics, never on PnL or trade outcomes.\n\n"
        "No provider query, backtest, paper/live trading or strategy promotion was performed.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def _all_false(payload: dict[str, Any], keys: list[str]) -> bool:
    return all(payload.get(key) is False for key in keys)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = pd.DataFrame(rows, columns=fieldnames)
        writer.to_csv(handle, index=False)


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "DOLLARBAR_TRANSFORM_PREREGISTRATION_PASS" if failed == 0 else "DOLLARBAR_TRANSFORM_PREREGISTRATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
