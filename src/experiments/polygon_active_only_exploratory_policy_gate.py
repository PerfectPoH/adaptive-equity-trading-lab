from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.experiments.polygon_active_only_exploratory_policy_gate_validator import (
    validate_polygon_active_only_exploratory_policy_gate,
)


RUN_ID = "POLYGON-ACTIVE-ONLY-EXPLORATORY-POLICY-GATE-RUN-001"
TRIAL_ID = "UNIVERSE-ACTIVE-ONLY-EXPLORATORY-POLICY-GATE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_active_only_exploratory_policy_gate_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-ACTIVE-ONLY-EXPLORATORY-POLICY-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Active-Only-Exploratory-Policy-Gate-2026-05-24.md")


def run_polygon_active_only_exploratory_policy_gate(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    preflight = validate_polygon_active_only_exploratory_policy_gate(spec_dir)
    _write_json(output / "preflight_report.json", preflight)
    if preflight["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
    else:
        manifest = _read_json(Path(spec_dir) / "policy_manifest.json")
        active = _read_json(Path(manifest["active_seed_decision"]))
        liquidity = _read_json(Path(manifest["liquidity_probe_decision"]))
        delisted = _read_json(Path(manifest["delisted_listing_date_probe_decision"]))
        decision = evaluate_active_only_exploratory_policy(active, liquidity, delisted)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def evaluate_active_only_exploratory_policy(
    active_decision: dict[str, Any],
    liquidity_decision: dict[str, Any],
    delisted_listing_date_decision: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if active_decision.get("decision") != "POLYGON_ACTIVE_UNIVERSE_SEED_PASS":
        blockers.append("active_seed_not_passed")
    if liquidity_decision.get("decision") != "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS":
        blockers.append("liquidity_probe_not_passed")
    if delisted_listing_date_decision.get("decision") != "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED":
        blockers.append("delisted_listing_date_blocker_not_documented")
    allowed = not blockers
    mandatory_caveats = [
        "active_only_survivorship_bias_declared",
        "no_survivorship_free_claim",
        "no_strategy_promotion",
        "no_live_or_paper_trading",
        "exploratory_research_only",
    ]
    return {
        "status": "complete" if allowed else "blocked",
        "decision": "POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_ALLOWED_NO_PROMOTION" if allowed else "POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "active_seed_count": active_decision.get("active_common_stock_seed_count", 0),
        "single_day_liquid_candidate_count": liquidity_decision.get("liquid_candidate_count", 0),
        "delisted_listing_date_decision": delisted_listing_date_decision.get("decision", ""),
        "delisted_listing_date_present_count": delisted_listing_date_decision.get("list_date_present_count", 0),
        "active_only_exploratory_research_allowed": allowed,
        "mandatory_caveats": mandatory_caveats,
        "blockers": blockers,
        "survivorship_free_claim_allowed": False,
        "strategy_promotion_allowed": False,
        "broad_survivorship_free_backtest_allowed": False,
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Preregister an active-only exploratory strategy trial with survivorship-bias caveat and no-promotion rule, or acquire a provider with delisted listing dates for full PIT research.",
    }


def validate_polygon_active_only_exploratory_policy_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    for filename in ["preflight_report.json", "final_decision.json"]:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = _read_json(path / "final_decision.json")
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "survivorship_claim_blocked", decision.get("survivorship_free_claim_allowed") is False, str(decision.get("survivorship_free_claim_allowed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False and decision.get("strategy_promotion_allowed") is False, str(decision))
    _check(checks, "paper_live_blocked", decision.get("paper_trading_performed") is False and decision.get("live_trading_performed") is False, str(decision))
    return _report(checks)


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "active_only_exploratory_research_allowed": False,
        "survivorship_free_claim_allowed": False,
        "strategy_promotion_allowed": False,
        "broad_survivorship_free_backtest_allowed": False,
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Active-Only Exploratory Policy Gate - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "No-query governance gate for active-only exploratory research after the delisted listing-date blocker. No provider query, market-data download, strategy backtest, execution, short selling, or promotion occurred.\n\n"
        "## Authorization\n\n"
        f"- Active-only exploratory research allowed: {decision.get('active_only_exploratory_research_allowed')}\n"
        f"- Survivorship-free claim allowed: {decision.get('survivorship_free_claim_allowed')}\n"
        f"- Strategy promotion allowed: {decision.get('strategy_promotion_allowed')}\n"
        f"- Broad survivorship-free backtest allowed: {decision.get('broad_survivorship_free_backtest_allowed')}\n"
        f"- Mandatory caveats: {', '.join(decision.get('mandatory_caveats', []))}\n\n"
        "## Interpretation\n\n"
        "The current free Polygon stack may support explicitly caveated active-only exploratory trials, but it cannot support survivorship-free broad-universe alpha claims or promoted strategies without delisted listing-date coverage.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon active-only exploratory policy gate.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_polygon_active_only_exploratory_policy_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_polygon_active_only_exploratory_policy_gate(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
