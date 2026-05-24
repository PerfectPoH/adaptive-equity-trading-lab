from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.experiments.research_program_transition_policy_gate_validator import (
    validate_research_program_transition_policy_gate,
)


RUN_ID = "RESEARCH-PROGRAM-TRANSITION-POLICY-GATE-RUN-001"
TRIAL_ID = "RESEARCH-PROGRAM-TRANSITION-POLICY-GATE-001"
SPEC_DIR = Path("experiments/provider_aware_research/research_program_transition_policy_gate_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/RESEARCH-PROGRAM-TRANSITION-POLICY-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Research-Program-Transition-Policy-Gate-2026-05-24.md")


def run_research_program_transition_policy_gate(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    preflight = validate_research_program_transition_policy_gate(spec_dir)
    _write_json(output / "preflight_report.json", preflight)
    if preflight["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
    else:
        manifest = _read_json(Path(spec_dir) / "policy_manifest.json")
        active_only = _read_json(Path(manifest["active_only_policy_decision"]))
        robustness = _read_json(Path(manifest["active_only_robustness_decision"]))
        delisted = _read_json(Path(manifest["delisted_listing_date_probe_decision"]))
        decision = evaluate_research_program_transition_policy(active_only, robustness, delisted)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def evaluate_research_program_transition_policy(
    active_only_policy: dict[str, Any],
    active_only_robustness: dict[str, Any],
    delisted_listing_date: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if active_only_policy.get("decision") != "POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_ALLOWED_NO_PROMOTION":
        blockers.append("active_only_policy_not_passed")
    if active_only_robustness.get("top3_dependency_flag") is not True:
        blockers.append("active_only_robustness_top3_dependency_not_documented")
    if delisted_listing_date.get("decision") != "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED":
        blockers.append("delisted_listing_date_blocker_not_documented")
    allowed = not blockers
    return {
        "status": "complete" if allowed else "blocked",
        "decision": "RESEARCH_PROGRAM_TRANSITION_ACTIVE" if allowed else "RESEARCH_PROGRAM_TRANSITION_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "smallcap_free_data_directional_research_allowed": False,
        "smallcap_free_data_directional_research_status": "PAUSED",
        "smallcap_microstructure_diagnostic_allowed": allowed,
        "smallcap_catalyst_diagnostic_allowed": allowed,
        "smallcap_data_quality_diagnostic_allowed": allowed,
        "smallcap_risk_management_diagnostic_allowed": allowed,
        "etf_largecap_risk_regime_lab_allowed": allowed,
        "strategy_promotion_allowed": False,
        "promotion_allowed": False,
        "survivorship_free_claim_allowed": False,
        "primary_data_blockers": ["delisted_listing_dates_unavailable_for_full_pit"],
        "active_only_failure_modes": ["top3_dependency", "negative_ex_top3_net_return", "negative_median_net_return"],
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
        "blockers": blockers,
        "next_unblocked_step": "Preregister ETF/large-cap risk/regime diagnostics or small-cap intraday/catalyst diagnostics only; do not reopen small-cap free-data directional alpha trials without new PIT data.",
    }


def validate_research_program_transition_policy_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
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
    _check(checks, "smallcap_directional_blocked", decision.get("smallcap_free_data_directional_research_allowed") is False, str(decision.get("smallcap_free_data_directional_research_allowed")))
    _check(checks, "diagnostics_allowed", decision.get("smallcap_microstructure_diagnostic_allowed") is True, str(decision.get("smallcap_microstructure_diagnostic_allowed")))
    _check(checks, "etf_largecap_lab_allowed", decision.get("etf_largecap_risk_regime_lab_allowed") is True, str(decision.get("etf_largecap_risk_regime_lab_allowed")))
    _check(checks, "promotion_blocked", decision.get("strategy_promotion_allowed") is False and decision.get("promotion_allowed") is False, str(decision))
    return _report(checks)


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "strategy_promotion_allowed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Research Program Transition Policy Gate - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "No-query governance gate transitioning the lab after the small-cap/free-data directional campaign. No market-data download, strategy backtest, execution, short selling, or promotion occurred.\n\n"
        "## Routing\n\n"
        f"- Small-cap/free-data directional research allowed: {decision['smallcap_free_data_directional_research_allowed']}\n"
        f"- Small-cap microstructure diagnostics allowed: {decision['smallcap_microstructure_diagnostic_allowed']}\n"
        f"- ETF/large-cap risk/regime lab allowed: {decision['etf_largecap_risk_regime_lab_allowed']}\n"
        f"- Strategy promotion allowed: {decision['strategy_promotion_allowed']}\n"
        f"- Primary data blockers: {', '.join(decision['primary_data_blockers'])}\n"
        f"- Active-only failure modes: {', '.join(decision['active_only_failure_modes'])}\n\n"
        "## Interpretation\n\n"
        "The lab should stop retesting small-cap free-data directional alpha in its current form. Small-cap remains useful for diagnostics; ETF/large-cap is opened only for cleaner-data risk/regime research, not for easy-alpha claims.\n"
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
    parser = argparse.ArgumentParser(description="Run research program transition policy gate.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_research_program_transition_policy_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_research_program_transition_policy_gate(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
