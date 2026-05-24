from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.experiments.polygon_pit_membership_policy_gate_validator import validate_polygon_pit_membership_policy_gate


RUN_ID = "POLYGON-PIT-MEMBERSHIP-POLICY-GATE-RUN-001"
TRIAL_ID = "UNIVERSE-PIT-POLICY-GATE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_pit_membership_policy_gate_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-PIT-MEMBERSHIP-POLICY-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-PIT-Membership-Policy-Gate-001-2026-05-24.md")


def run_polygon_pit_membership_policy_gate_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    active_decision_path: str | Path | None = None,
    liquidity_decision_path: str | Path | None = None,
    delisted_decision_path: str | Path | None = None,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_pit_membership_policy_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
    else:
        manifest = json.loads((Path(spec_dir) / "policy_manifest.json").read_text(encoding="utf-8"))
        active = _read_json(Path(active_decision_path) if active_decision_path else Path(manifest["active_seed_decision"]))
        liquidity = _read_json(Path(liquidity_decision_path) if liquidity_decision_path else Path(manifest["liquidity_probe_decision"]))
        delisted = _read_json(Path(delisted_decision_path) if delisted_decision_path else Path(manifest["delisted_audit_decision"]))
        decision = evaluate_polygon_pit_membership_policy(active, liquidity, delisted)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def evaluate_polygon_pit_membership_policy(
    active_decision: dict[str, Any],
    liquidity_decision: dict[str, Any],
    delisted_decision: dict[str, Any],
) -> dict[str, Any]:
    single_day_blockers: list[str] = []
    if active_decision.get("decision") != "POLYGON_ACTIVE_UNIVERSE_SEED_PASS":
        single_day_blockers.append("active_seed_not_passed")
    if liquidity_decision.get("decision") != "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS":
        single_day_blockers.append("liquidity_probe_not_passed")
    if delisted_decision.get("decision") != "POLYGON_DELISTED_METADATA_SUPPORT_PASS":
        single_day_blockers.append("delisted_metadata_support_not_passed")
    single_day_allowed = not single_day_blockers
    broad_blockers = ["listing_dates_unavailable", "asof_membership_history_unconstructed"]
    return {
        "status": "complete",
        "decision": "POLYGON_DATA_STACK_READY_SINGLE_DAY_ONLY" if single_day_allowed else "POLYGON_DATA_STACK_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "active_seed_count": active_decision.get("active_common_stock_seed_count", 0),
        "matched_seed_bar_count": liquidity_decision.get("matched_seed_bar_count", 0),
        "single_day_liquid_candidate_count": liquidity_decision.get("liquid_candidate_count", 0),
        "delisted_common_stock_count": delisted_decision.get("delisted_common_stock_count", 0),
        "single_day_liquid_snapshot_allowed": single_day_allowed,
        "single_day_blockers": single_day_blockers,
        "broad_universe_backtest_allowed": False,
        "broad_backtest_blockers": broad_blockers,
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Preregister a PIT membership construction method with listing dates/as-of membership before any broad-universe backtest; single-day non-alpha diagnostics may use the liquid snapshot.",
    }


def validate_polygon_pit_membership_policy_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    for filename in ["preflight_report.json", "final_decision.json"]:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = _read_json(path / "final_decision.json")
    _check(checks, "provider_query_not_performed", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "market_download_not_performed", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "backtest_not_performed", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "broad_blockers_present", {"listing_dates_unavailable", "asof_membership_history_unconstructed"}.issubset(set(decision.get("broad_backtest_blockers", []))), str(decision.get("broad_backtest_blockers")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _report(checks)


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "single_day_liquid_snapshot_allowed": False,
        "broad_universe_backtest_allowed": False,
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon PIT Membership Policy Gate 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Authorization Result\n\n"
        f"- Single-day liquid snapshot allowed: {decision.get('single_day_liquid_snapshot_allowed')}\n"
        f"- Broad-universe backtest allowed: {decision.get('broad_universe_backtest_allowed')}\n"
        f"- Broad backtest blockers: {', '.join(decision.get('broad_backtest_blockers', []))}\n"
        f"- Provider query performed: {decision.get('provider_query_performed')}\n"
        f"- Market data downloaded: {decision.get('market_data_downloaded')}\n"
        f"- Backtest performed: {decision.get('backtest_performed')}\n\n"
        "## Interpretation\n\n"
        "The Polygon data stack is sufficient for single-day non-alpha liquidity diagnostics, but not for broad historical universe backtests. Listing dates and as-of membership history remain unconstructed.\n"
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
        "gate_decision": "POLYGON_PIT_MEMBERSHIP_POLICY_OUTPUT_PASS" if failed == 0 else "POLYGON_PIT_MEMBERSHIP_POLICY_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon PIT membership policy gate.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_polygon_pit_membership_policy_gate_001()
    report = validate_polygon_pit_membership_policy_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
