from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


TRIAL_ID = "TRIAL-PEAD-EARNINGS-001"
PREREG_ID = "PREREG-PEAD-EARNINGS-001"
RUN_ID = "PEAD-EARNINGS-ONLY-GATE-001"
ROOT = Path("experiments/provider_aware_research")
ARTIFACT_DIR = ROOT / "pead_earnings_only_gate_20260521"
INTRINIO_PROBE_RESULT = ROOT / "execution_outputs" / "XMOM-EARNINGS-SINGLE-PROBE-001" / "single_probe_execution_manifest.json"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-Earnings-Only-Gate-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-pead-earnings-only-gate.md")


def run_pead_earnings_only_gate() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    prereg = _write_preregistration()
    provider_review = _write_provider_access_review()
    pre_run = _write_pre_run_gate(prereg, provider_review)
    decision = _write_final_decision(prereg, provider_review, pre_run)
    return decision


def validate_pead_earnings_only_gate(gate_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(gate_dir)
    checks: list[dict[str, Any]] = []
    required_files = [
        "pead_preregistration_manifest.json",
        "feature_contract.csv",
        "blocked_actions.csv",
        "provider_access_review.json",
        "pre_run_gate_report.json",
        "final_decision.json",
    ]
    _check(checks, "gate_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required_files:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)
    prereg = json.loads((path / "pead_preregistration_manifest.json").read_text(encoding="utf-8"))
    provider = json.loads((path / "provider_access_review.json").read_text(encoding="utf-8"))
    pre_run = json.loads((path / "pre_run_gate_report.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    _check(checks, "earnings_only_scope", prereg.get("scope") == "earnings_only", str(prereg.get("scope")))
    _check(checks, "daily_gap_trigger_forbidden", prereg.get("daily_gap_trigger_allowed") is False, str(prereg.get("daily_gap_trigger_allowed")))
    _check(checks, "report_time_required", prereg.get("requires_bmo_amc_report_time") is True, str(prereg.get("requires_bmo_amc_report_time")))
    _check(checks, "provider_access_blocked_by_403", provider.get("provider_error") == "HTTP_ERROR_403", str(provider.get("provider_error")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "decision_blocked_not_promoted", decision.get("decision") == "BLOCKED_PROVIDER_EARNINGS_CALENDAR_UNAVAILABLE", str(decision.get("decision")))
    _check(checks, "pre_run_gate_failed_closed", pre_run.get("status") == "blocked", str(pre_run.get("status")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create and validate PEAD earnings-only gate.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_pead_earnings_only_gate()
    report = validate_pead_earnings_only_gate()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _write_preregistration() -> dict[str, Any]:
    manifest = {
        "status": "PREREGISTERED_BLOCKED_PENDING_EARNINGS_PROVIDER",
        "trial_id": TRIAL_ID,
        "preregistration_id": PREREG_ID,
        "run_id": RUN_ID,
        "hypothesis": "Post-earnings announcement drift can survive conservative execution costs over a multi-day holding window when events are timestamped by BMO/AMC reaction session.",
        "scope": "earnings_only",
        "requires_bmo_amc_report_time": True,
        "requires_historical_earnings_calendar": True,
        "requires_surprise_or_event_magnitude": True,
        "daily_gap_trigger_allowed": False,
        "manual_catalyst_log_allowed_as_event_source": False,
        "holding_window": "multi_day_tbd_after_provider_gate",
        "round_trip_cost_bps": 500.0,
        "minimum_trades_for_promotion": 30,
        "dsr_threshold": 0.95,
        "parameter_sweep_allowed": False,
    }
    _write_json(ARTIFACT_DIR / "pead_preregistration_manifest.json", manifest)
    _write_csv(
        ARTIFACT_DIR / "feature_contract.csv",
        ["feature", "status", "rule"],
        [
            ["earnings_event_timestamp", "required", "Must map to BMO/AMC reaction session; DMT/UNSPECIFIED purged."],
            ["earnings_surprise_or_magnitude", "required", "Must be defined before execution; no PnL-derived thresholds."],
            ["post_earnings_holding_window", "blocked_tbd", "Cannot freeze before event-source viability."],
            ["daily_gap_trigger", "forbidden", "Daily OHLC gap cannot define PEAD events."],
            ["manual_forensics_events", "forbidden", "XMOM forensics cannot seed PEAD trial events."],
        ],
    )
    _write_csv(
        ARTIFACT_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["backtest", "blocked", "No historical earnings calendar with report-time metadata is available."],
            ["use_manual_catalyst_log", "blocked", "Manual forensics would contaminate PEAD event selection."],
            ["use_daily_gap_proxy", "blocked", "Daily gap proxy already failed as intraday/event trigger."],
            ["paper_trading", "blocked", "No validated strategy."],
            ["live_trading", "blocked", "No validated strategy."],
            ["strategy_promotion", "blocked", "Provider gate unresolved and no DSR."],
        ],
    )
    return manifest


def _write_provider_access_review() -> dict[str, Any]:
    previous = {}
    if INTRINIO_PROBE_RESULT.exists():
        previous = json.loads(INTRINIO_PROBE_RESULT.read_text(encoding="utf-8"))
    review = {
        "status": "blocked",
        "trial_id": TRIAL_ID,
        "evidence_source": str(INTRINIO_PROBE_RESULT),
        "provider_reviewed": previous.get("provider", "Intrinio"),
        "endpoint_reviewed": previous.get("endpoint", "companies/{identifier}/upcoming_earnings"),
        "provider_error": previous.get("error", "missing_prior_probe"),
        "provider_detail": previous.get("detail", ""),
        "raw_payload_retained": previous.get("raw_payload_retained", False),
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "conclusion": "Current earnings-calendar/report-time provider access is unavailable; PEAD execution must remain blocked.",
    }
    _write_json(ARTIFACT_DIR / "provider_access_review.json", review)
    return review


def _write_pre_run_gate(prereg: dict[str, Any], provider_review: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("preregistration_exists", prereg.get("status") == "PREREGISTERED_BLOCKED_PENDING_EARNINGS_PROVIDER"),
        ("earnings_only_scope", prereg.get("scope") == "earnings_only"),
        ("provider_access_available", provider_review.get("status") == "pass"),
        ("report_time_metadata_available", False),
        ("manual_event_substitution_forbidden", prereg.get("manual_catalyst_log_allowed_as_event_source") is False),
    ]
    report = {
        "status": "pass" if all(ok for _, ok in checks) else "blocked",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "checks": [{"name": name, "status": "pass" if ok else "fail"} for name, ok in checks],
        "backtest_authorized": False,
    }
    _write_json(ARTIFACT_DIR / "pre_run_gate_report.json", report)
    return report


def _write_final_decision(prereg: dict[str, Any], provider_review: dict[str, Any], pre_run: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "blocked",
        "decision": "BLOCKED_PROVIDER_EARNINGS_CALENDAR_UNAVAILABLE",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "preregistration_status": prereg.get("status"),
        "provider_status": provider_review.get("status"),
        "pre_run_status": pre_run.get("status"),
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Resolve historical earnings calendar/report-time provider access with one approved provider probe.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, provider_review)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], provider_review: dict[str, Any]) -> str:
    return (
        "# Report PEAD Earnings-Only Gate - 2026-05-21\n\n"
        f"Decision: {decision['decision']}\n\n"
        "## Why It Is Blocked\n"
        f"- Prior provider: {provider_review.get('provider_reviewed')}\n"
        f"- Prior endpoint: {provider_review.get('endpoint_reviewed')}\n"
        f"- Prior result: {provider_review.get('provider_error')} / {provider_review.get('provider_detail')}\n"
        "- New provider query performed now: false\n"
        "- Backtest performed: false\n\n"
        "## Interpretation\n"
        "PEAD earnings-only is the right next hypothesis structurally, but it cannot be executed from manual catalyst logs, "
        "daily gap proxies, or earnings dates without BMO/AMC report-time quality. The gate is therefore closed until the "
        "earnings-calendar provider access problem is resolved.\n"
    )


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "PEAD_EARNINGS_ONLY_GATE_PASS_BLOCKED_CLOSED" if failed == 0 else "PEAD_EARNINGS_ONLY_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
