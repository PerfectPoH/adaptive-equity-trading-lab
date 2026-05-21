from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_ID = "ALPHA-CANDIDATE-FACTORY-001"
ARTIFACT_DIR = Path("experiments/provider_aware_research/alpha_candidate_factory_20260521")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Alpha-Candidate-Factory-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-alpha-candidate-factory.md")

REQUIRED_COLUMNS = {
    "candidate_id",
    "hypothesis",
    "market_mechanism",
    "required_data",
    "provider_dependency",
    "cost_realism",
    "primary_failure_mode",
    "minimum_probe",
    "blocked_until",
    "priority_score",
    "decision",
}

FORBIDDEN_DECISIONS = {"run_backtest", "paper_trade", "live_trade", "promote_strategy"}


def run_alpha_candidate_factory() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = build_alpha_candidates()
    ranked = rank_candidates(candidates)
    _write_csv(ARTIFACT_DIR / "alpha_candidates.csv", list(ranked[0].keys()), ranked)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    manifest = _write_manifest(ranked)
    decision = _write_decision(manifest, ranked)
    return decision


def build_alpha_candidates() -> list[dict[str, Any]]:
    return [
        _candidate(
            "ALPHA-001",
            "Post-earnings SUE drift on small-cap earnings with official point-in-time consensus.",
            "Slow information diffusion after earnings surprise.",
            "SEC EDGAR Item 2.02 timestamps + PIT consensus/actual EPS + RTH bars",
            "blocked_requires_pit_sue_provider",
            "high",
            "No entitlement to SUE provider or costs consume drift.",
            "One-call SUE schema probe on CRMD, no backtest.",
            "PIT SUE provider entitlement verified",
            62,
            "blocked_provider_dependency",
        ),
        _candidate(
            "ALPHA-002",
            "Opening reclaim after RTH-native gap-down only if spread-adjusted edge survives 500 bps.",
            "Intraday overreaction and liquidity absorption after regular-session dislocation.",
            "Existing Databento RTH bars + spread proxy + cost model",
            "available_partial_intraday_bars",
            "strict_500bps",
            "Gross edge exists but is too thin after taker costs.",
            "Spec-only cost sensitivity using already stored mini-panel outputs.",
            "Cost realism gate already mandatory",
            54,
            "archive_or_low_priority_probe",
        ),
        _candidate(
            "ALPHA-003",
            "Dollar-bar version of opening reclaim reduces time-bar noise before strategy logic.",
            "Variance stabilization by sampling on traded notional instead of clock time.",
            "Databento trades or 1m bars with dollar volume; no L3 required",
            "requires_trade_or_bar_data",
            "medium",
            "Dollar bars improve estimation but do not create alpha by themselves.",
            "Build transformer on stored bars and compare distribution diagnostics only.",
            "No strategy signal until data transform validator exists",
            78,
            "best_infrastructure_probe",
        ),
        _candidate(
            "ALPHA-004",
            "Amihud illiquidity filter separates tradable small-cap drifts from cost traps.",
            "Illiquidity premium exists but can be untradeable unless capacity is modeled.",
            "Daily OHLCV with dollar volume + corporate action caveats",
            "available_caveated_daily",
            "strict_capacity_required",
            "Illiquid winners vanish after impact and spread.",
            "Compute Amihud distributions only; no entry signal.",
            "Provider coverage contract for daily data",
            69,
            "research_feature_probe",
        ),
        _candidate(
            "ALPHA-005",
            "Quality-filtered small-cap momentum avoids junk-driven size anomaly decay.",
            "Size premium reappears after excluding low-quality firms.",
            "Fundamental quality fields + PIT market cap + prices",
            "blocked_requires_fundamental_provider",
            "medium_high",
            "Quality fields are stale, non-PIT, or survivorship-biased.",
            "Provider schema entitlement probe for PIT fundamentals.",
            "PIT fundamentals provider verified",
            58,
            "blocked_provider_dependency",
        ),
        _candidate(
            "ALPHA-006",
            "Biotech pre-catalyst drift exits before binary readout to avoid coin-flip exposure.",
            "Speculative positioning into known FDA/PDUFA or clinical readout windows.",
            "Biotech catalyst calendar + prices + options/liquidity optional",
            "blocked_requires_catalyst_calendar",
            "high",
            "Calendar incomplete or single-asset blowups dominate.",
            "Provider/source audit for PDUFA/readout calendar only.",
            "Catalyst calendar quality gate",
            64,
            "blocked_provider_dependency",
        ),
        _candidate(
            "ALPHA-007",
            "Same-day bad-news fade avoidance: no long reversion if SEC event is fundamental break.",
            "Some gap-downs are breakaway repricings, not overreaction.",
            "SEC 8-K item taxonomy + RTH bars",
            "sec_available_price_available",
            "strict_500bps",
            "Event taxonomy too coarse to distinguish fraud, dilution, and earnings.",
            "Classifier-free rule audit on SEC item codes only.",
            "No NLP or return-inferred labels",
            71,
            "research_filter_probe",
        ),
        _candidate(
            "ALPHA-008",
            "Provider sensitivity arbitrage is not alpha but can identify data-fragile hypotheses early.",
            "Signals that flip across providers are likely data artifacts.",
            "Databento + Polygon/other overlap summaries",
            "available_partial_overlap",
            "not_strategy",
            "Becomes a meta-test, not a return source.",
            "Add provider fragility score to candidate ranking.",
            "No trading allowed",
            73,
            "meta_infrastructure_probe",
        ),
        _candidate(
            "ALPHA-009",
            "Outlier-resistant cross-sectional ranking using median trade contribution, not total PnL.",
            "Robust estimators reduce dependence on one explosive small-cap winner.",
            "Existing trade logs + candidate logs",
            "available_existing_artifacts",
            "not_strategy",
            "May only make bad strategies fail faster.",
            "Run on historical artifacts as diagnostics, no new market data.",
            "Diagnostic-only harness",
            82,
            "best_diagnostic_probe",
        ),
        _candidate(
            "ALPHA-010",
            "Cooldown and BAD_WIN exclusion improve live survivability but do not create alpha.",
            "Execution psychology can be enforced as code.",
            "Trade governance runtime logs",
            "available_local_runtime",
            "not_strategy",
            "Governance reduces errors but cannot rescue negative expectancy.",
            "Integrate governance tags into future post-run validator.",
            "No broker integration",
            76,
            "best_governance_integration",
        ),
        _candidate(
            "ALPHA-011",
            "Macro-regime switch disables high-beta small-cap signals during stress.",
            "Small-cap anomalies can invert when liquidity regime breaks.",
            "IWM/VIX/breadth + strategy candidate logs",
            "available_partial_indices",
            "medium",
            "Regime filter overfits and removes all sample size.",
            "Spec-only ablation on existing failed trials.",
            "No threshold chosen from OOS PnL",
            66,
            "research_filter_probe",
        ),
        _candidate(
            "ALPHA-012",
            "Order-flow absorption trigger for gap-downs using L3/L2 replaces VWAP reclaim.",
            "Passive institutional absorption can reveal exhaustion of forced selling.",
            "Databento MBO/MBP or equivalent order-book feed",
            "blocked_requires_l2_l3_data_budget",
            "high_infrastructure_cost",
            "Data volume and compute cost exceed current lab scope.",
            "Spec-only order-book data contract, no download.",
            "Order-book budget and parser plan",
            49,
            "defer_year_2",
        ),
    ]


def rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda row: int(row["priority_score"]), reverse=True)


def validate_alpha_candidate_factory(factory_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(factory_dir)
    checks: list[dict[str, Any]] = []
    required_files = ["alpha_candidates.csv", "blocked_actions.csv", "alpha_candidate_factory_manifest.json", "final_decision.json"]
    _check(checks, "factory_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required_files:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)

    candidates = _read_csv(path / "alpha_candidates.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    manifest = json.loads((path / "alpha_candidate_factory_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(candidates[0].keys()) if candidates else set()
    decisions = {row["decision"] for row in candidates}
    scores = [int(row["priority_score"]) for row in candidates]

    _check(checks, "candidate_count_minimum_10", len(candidates) >= 10, f"candidates={len(candidates)}")
    _check(checks, "required_columns_present", REQUIRED_COLUMNS.issubset(columns), f"missing={sorted(REQUIRED_COLUMNS - columns)}")
    _check(checks, "no_forbidden_candidate_decisions", decisions.isdisjoint(FORBIDDEN_DECISIONS), f"decisions={sorted(decisions)}")
    _check(checks, "ranked_descending", scores == sorted(scores, reverse=True), f"scores={scores}")
    _check(checks, "has_provider_blocked_candidates", any(row["decision"] == "blocked_provider_dependency" for row in candidates), "provider blockers present")
    _check(checks, "has_local_diagnostic_candidate", any(row["decision"] == "best_diagnostic_probe" for row in candidates), "diagnostic candidate present")
    _check(checks, "has_infrastructure_candidate", any("infrastructure" in row["decision"] for row in candidates), "infrastructure candidate present")
    _check(checks, "all_candidates_have_failure_modes", all(row["primary_failure_mode"].strip() for row in candidates), "failure modes populated")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked actions")
    _check(checks, "manifest_no_execution", manifest.get("backtest_performed") is False and manifest.get("provider_query_performed") is False, str(manifest))
    _check(checks, "decision_factory_ready", decision.get("decision") == "ALPHA_CANDIDATE_FACTORY_READY_NO_EXECUTION", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a spec-only alpha candidate factory.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_alpha_candidate_factory()
    report = validate_alpha_candidate_factory()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _candidate(
    candidate_id: str,
    hypothesis: str,
    market_mechanism: str,
    required_data: str,
    provider_dependency: str,
    cost_realism: str,
    primary_failure_mode: str,
    minimum_probe: str,
    blocked_until: str,
    priority_score: int,
    decision: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "hypothesis": hypothesis,
        "market_mechanism": market_mechanism,
        "required_data": required_data,
        "provider_dependency": provider_dependency,
        "cost_realism": cost_realism,
        "primary_failure_mode": primary_failure_mode,
        "minimum_probe": minimum_probe,
        "blocked_until": blocked_until,
        "priority_score": priority_score,
        "decision": decision,
    }


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["run_candidate_backtest", "blocked", "Candidates are ranked ideas, not executable trials."],
        ["select_threshold_from_old_pnl", "blocked", "Would reuse falsified samples as optimization data."],
        ["paper_trade_candidate", "blocked", "No candidate has passed preregistration, data, CPCV and DSR gates."],
        ["live_trade_candidate", "blocked", "No candidate is strategy-promotable."],
        ["provider_query", "blocked", "Each provider-dependent candidate requires its own one-call approval gate."],
    ]


def _write_manifest(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    top = candidates[0]
    manifest = {
        "status": "ready_not_executable",
        "decision": "ALPHA_CANDIDATE_FACTORY_READY_NO_EXECUTION",
        "run_id": RUN_ID,
        "candidate_count": len(candidates),
        "top_candidate_id": top["candidate_id"],
        "top_candidate_decision": top["decision"],
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(ARTIFACT_DIR / "alpha_candidate_factory_manifest.json", manifest)
    return manifest


def _write_decision(manifest: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    decision = {
        "status": "ready_not_executable",
        "decision": "ALPHA_CANDIDATE_FACTORY_READY_NO_EXECUTION",
        "run_id": RUN_ID,
        "candidate_count": len(candidates),
        "top_next_step": "Implement diagnostic-only outlier-resistant candidate ranking harness on existing artifacts.",
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, manifest, candidates[:5])
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], manifest: dict[str, Any], top_candidates: list[dict[str, Any]]) -> str:
    top_rows = "\n".join(
        f"- {row['candidate_id']} ({row['priority_score']}): {row['decision']} - {row['hypothesis']}"
        for row in top_candidates
    )
    return (
        "# Report Alpha Candidate Factory - 2026-05-21\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Purpose\n\n"
        "The lab has strong falsification infrastructure but no validated profitable strategy. "
        "This factory creates a ranked queue of small, falsifiable candidates without authorizing execution.\n\n"
        "## Top Candidates\n\n"
        f"{top_rows}\n\n"
        "## Guardrails\n\n"
        "- No provider query.\n"
        "- No backtest.\n"
        "- No threshold selection from old PnL.\n"
        "- No paper/live trading.\n"
        "- Every candidate declares its primary failure mode before any future probe.\n\n"
        f"Next safe step: {decision['top_next_step']}\n"
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
        "gate_decision": "ALPHA_CANDIDATE_FACTORY_PASS_READY_NOT_EXECUTABLE" if failed == 0 else "ALPHA_CANDIDATE_FACTORY_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
