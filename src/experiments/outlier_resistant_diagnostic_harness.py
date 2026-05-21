from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any


RUN_ID = "OUTLIER-RESISTANT-DIAGNOSTIC-001"
ARTIFACT_DIR = Path("experiments/provider_aware_research/outlier_resistant_diagnostic_20260521")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Outlier-Resistant-Diagnostic-Harness-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-outlier-resistant-diagnostic-harness.md")

DEFAULT_PANEL = [
    {
        "candidate_id": "DX-XMOM-001",
        "label": "XMOM trial 001",
        "path": "experiments/runs/xmom_trial_001_20260520/portfolio_trade_log.csv",
    },
    {
        "candidate_id": "DX-RANKEX-001",
        "label": "RankEx validation 2024",
        "path": "experiments/runs/small_cap_rankex_trial_001_validation_2024/portfolio_trade_log.csv",
    },
    {
        "candidate_id": "DX-OOS-2025-RISK",
        "label": "Small-cap OOS 2025 full risk sizing",
        "path": "experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_full_risk_sizing_20260512/portfolio_trade_log.csv",
    },
    {
        "candidate_id": "DX-PROVIDER-REPLAY",
        "label": "Provider-aware bounded replay",
        "path": "experiments/runs/provider_aware_oos_replay_bounded_20260520/portfolio_trade_log.csv",
    },
]


def run_outlier_resistant_diagnostic_harness() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    diagnostics = [diagnose_trade_log(row["candidate_id"], row["label"], Path(row["path"])) for row in DEFAULT_PANEL]
    diagnostics = sorted(diagnostics, key=lambda row: (row["robustness_score"], row["trade_count"]), reverse=True)
    _write_csv(ARTIFACT_DIR / "diagnostic_panel.csv", list(diagnostics[0].keys()), diagnostics)
    _write_csv(ARTIFACT_DIR / "input_panel.csv", ["candidate_id", "label", "path"], DEFAULT_PANEL)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    manifest = _write_manifest(diagnostics)
    decision = _write_decision(manifest, diagnostics)
    return decision


def diagnose_trade_log(candidate_id: str, label: str, path: Path) -> dict[str, Any]:
    rows = _read_trade_rows(path)
    pnls = [float(row["pnl"]) for row in rows]
    returns = [float(row["return_pct"]) for row in rows if _has_number(row.get("return_pct", ""))]
    total_pnl = sum(pnls)
    sorted_pnls = sorted(pnls, reverse=True)
    top1_pnl = sum(sorted_pnls[:1])
    top3_pnl = sum(sorted_pnls[:3])
    pnl_ex_top1 = total_pnl - top1_pnl
    pnl_ex_top3 = total_pnl - top3_pnl
    trade_count = len(pnls)
    top1_contribution_pct = _contribution_pct(top1_pnl, total_pnl)
    top3_contribution_pct = _contribution_pct(top3_pnl, total_pnl)
    sign_flip_ex_top3 = total_pnl > 0 and pnl_ex_top3 <= 0
    median_pnl = median(pnls) if pnls else 0.0
    median_return = median(returns) if returns else 0.0
    win_rate = sum(1 for pnl in pnls if pnl > 0) / trade_count if trade_count else 0.0
    robustness_score = score_robustness(
        trade_count=trade_count,
        total_pnl=total_pnl,
        median_pnl=median_pnl,
        pnl_ex_top3=pnl_ex_top3,
        sign_flip_ex_top3=sign_flip_ex_top3,
        top3_contribution_pct=top3_contribution_pct,
    )
    return {
        "candidate_id": candidate_id,
        "label": label,
        "source_path": str(path),
        "trade_count": trade_count,
        "total_pnl": round(total_pnl, 6),
        "median_pnl": round(median_pnl, 6),
        "median_return_pct": round(median_return, 8),
        "win_rate": round(win_rate, 6),
        "top1_pnl": round(top1_pnl, 6),
        "top3_pnl": round(top3_pnl, 6),
        "top1_contribution_pct": round(top1_contribution_pct, 6),
        "top3_contribution_pct": round(top3_contribution_pct, 6),
        "pnl_excluding_top1": round(pnl_ex_top1, 6),
        "pnl_excluding_top3": round(pnl_ex_top3, 6),
        "sign_flip_excluding_top3": sign_flip_ex_top3,
        "robustness_score": robustness_score,
        "diagnostic_verdict": verdict_from_diagnostics(trade_count, total_pnl, median_pnl, pnl_ex_top3, sign_flip_ex_top3),
    }


def score_robustness(
    *,
    trade_count: int,
    total_pnl: float,
    median_pnl: float,
    pnl_ex_top3: float,
    sign_flip_ex_top3: bool,
    top3_contribution_pct: float,
) -> int:
    score = 0
    if trade_count >= 30:
        score += 25
    elif trade_count >= 10:
        score += 10
    if total_pnl > 0:
        score += 15
    if median_pnl > 0:
        score += 25
    if pnl_ex_top3 > 0:
        score += 25
    if not sign_flip_ex_top3:
        score += 10
    if abs(top3_contribution_pct) > 100:
        score -= 20
    elif abs(top3_contribution_pct) > 60:
        score -= 10
    return max(0, min(100, score))


def verdict_from_diagnostics(
    trade_count: int,
    total_pnl: float,
    median_pnl: float,
    pnl_ex_top3: float,
    sign_flip_ex_top3: bool,
) -> str:
    if trade_count < 10:
        return "INSUFFICIENT_TRADES_DIAGNOSTIC_ONLY"
    if total_pnl <= 0:
        return "NEGATIVE_TOTAL_PNL_NO_PROMOTION"
    if median_pnl <= 0:
        return "NEGATIVE_MEDIAN_TRADE_NO_PROMOTION"
    if pnl_ex_top3 <= 0 or sign_flip_ex_top3:
        return "OUTLIER_DEPENDENT_NO_PROMOTION"
    return "ROBUSTNESS_CANDIDATE_FOR_FUTURE_PREREGISTRATION"


def validate_outlier_resistant_diagnostic_harness(harness_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(harness_dir)
    checks: list[dict[str, Any]] = []
    required_files = ["diagnostic_panel.csv", "input_panel.csv", "blocked_actions.csv", "diagnostic_manifest.json", "final_decision.json"]
    _check(checks, "harness_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required_files:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)

    panel = _read_csv(path / "diagnostic_panel.csv")
    inputs = _read_csv(path / "input_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    manifest = json.loads((path / "diagnostic_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    required_columns = {
        "candidate_id",
        "trade_count",
        "total_pnl",
        "median_pnl",
        "pnl_excluding_top3",
        "sign_flip_excluding_top3",
        "robustness_score",
        "diagnostic_verdict",
    }
    columns = set(panel[0].keys()) if panel else set()
    scores = [int(row["robustness_score"]) for row in panel]
    _check(checks, "input_panel_is_explicit", len(inputs) == len(DEFAULT_PANEL), f"inputs={len(inputs)}")
    _check(checks, "diagnostic_panel_non_empty", len(panel) > 0, f"panel={len(panel)}")
    _check(checks, "required_columns_present", required_columns.issubset(columns), f"missing={sorted(required_columns - columns)}")
    _check(checks, "scores_ranked_descending", scores == sorted(scores, reverse=True), f"scores={scores}")
    forbidden_verdicts = {"PROMOTE", "STRATEGY_PROMOTION", "PAPER_TRADE_READY", "LIVE_TRADE_READY"}
    _check(
        checks,
        "no_promotional_verdicts",
        all(row["diagnostic_verdict"] not in forbidden_verdicts for row in panel),
        "diagnostic only",
    )
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked actions")
    _check(checks, "manifest_no_execution", manifest.get("backtest_performed") is False and manifest.get("provider_query_performed") is False, str(manifest))
    _check(checks, "decision_no_execution", decision.get("decision") == "OUTLIER_DIAGNOSTIC_COMPLETE_NO_EXECUTION", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run outlier-resistant diagnostics on existing trade-log artifacts.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_outlier_resistant_diagnostic_harness()
    report = validate_outlier_resistant_diagnostic_harness()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Diagnostic uses existing artifacts only."],
        ["run_backtest", "blocked", "No new performance run is authorized."],
        ["select_strategy_for_promotion", "blocked", "Harness ranks robustness candidates only."],
        ["paper_trading", "blocked", "No strategy has passed preregistration, data, CPCV and DSR gates."],
        ["live_trading", "blocked", "No strategy is promotable."],
    ]


def _write_manifest(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    top = diagnostics[0]
    manifest = {
        "status": "diagnostic_complete_not_executable",
        "decision": "OUTLIER_DIAGNOSTIC_COMPLETE_NO_EXECUTION",
        "run_id": RUN_ID,
        "panel_count": len(diagnostics),
        "top_candidate_id": top["candidate_id"],
        "top_candidate_verdict": top["diagnostic_verdict"],
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(ARTIFACT_DIR / "diagnostic_manifest.json", manifest)
    return manifest


def _write_decision(manifest: dict[str, Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    robust_candidates = [
        row["candidate_id"]
        for row in diagnostics
        if row["diagnostic_verdict"] == "ROBUSTNESS_CANDIDATE_FOR_FUTURE_PREREGISTRATION"
    ]
    decision = {
        "status": "diagnostic_complete_not_executable",
        "decision": "OUTLIER_DIAGNOSTIC_COMPLETE_NO_EXECUTION",
        "run_id": RUN_ID,
        "panel_count": len(diagnostics),
        "robustness_candidates_for_future_preregistration": robust_candidates,
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If any diagnostic candidate survives, create a separate preregistration spec before any new data or backtest.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, manifest, diagnostics)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], manifest: dict[str, Any], diagnostics: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"- {row['candidate_id']} score={row['robustness_score']} verdict={row['diagnostic_verdict']} "
        f"trades={row['trade_count']} total_pnl={row['total_pnl']} median_pnl={row['median_pnl']} "
        f"pnl_ex_top3={row['pnl_excluding_top3']}"
        for row in diagnostics
    )
    return (
        "# Report Outlier-Resistant Diagnostic Harness - 2026-05-21\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Diagnostic-only analysis of existing trade-log artifacts. No new provider query, market-data download, backtest, paper/live trading or strategy promotion was performed.\n\n"
        "## Ranking\n\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "The harness prioritizes median trade quality and positive PnL after removing the top three winners. "
        "It is designed to make outlier-dependent ideas fail before they receive any new execution budget.\n"
    )


def _read_trade_rows(path: Path) -> list[dict[str, str]]:
    rows = _read_csv(path)
    if not rows:
        raise ValueError(f"empty trade log: {path}")
    if "pnl" not in rows[0]:
        raise ValueError(f"trade log missing pnl column: {path}")
    return [row for row in rows if _has_number(row.get("pnl", ""))]


def _has_number(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _contribution_pct(part: float, total: float) -> float:
    if total == 0:
        return 0.0
    return (part / total) * 100


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
        "gate_decision": "OUTLIER_DIAGNOSTIC_HARNESS_PASS" if failed == 0 else "OUTLIER_DIAGNOSTIC_HARNESS_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
