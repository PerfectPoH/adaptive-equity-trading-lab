from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


TRIAL_ID = "TRIAL-PEAD-EARNINGS-001"
RUN_ID = "PEAD-SEC-EVENT-SOURCE-GATE-001"
ROOT = Path("experiments/provider_aware_research")
SEC_PROBE_DIR = ROOT / "sec_edgar_earnings_provider_probe_20260521"
SEC_SUMMARY = SEC_PROBE_DIR / "sec_edgar_earnings_8k_summary.csv"
ARTIFACT_DIR = ROOT / "pead_sec_event_source_gate_20260521"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-SEC-Event-Source-Gate-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-pead-sec-event-source-gate.md")
NY = ZoneInfo("America/New_York")


def run_pead_sec_event_source_gate(summary_path: str | Path = SEC_SUMMARY) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    events = build_sec_earnings_event_panel(summary_path)
    events.to_csv(ARTIFACT_DIR / "pead_sec_event_source_panel.csv", index=False)
    manifest = _write_manifest(events)
    decision = _write_decision(manifest)
    return decision


def build_sec_earnings_event_panel(summary_path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(summary_path)
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        classification = str(row.get("classification", ""))
        if classification not in {"BMO", "AMC"}:
            continue
        acceptance_utc = pd.Timestamp(row["acceptanceDateTime"], tz="UTC")
        reaction_session = _reaction_session_date(acceptance_utc, classification)
        rows.append(
            {
                "accessionNumber": row["accessionNumber"],
                "filingDate": row["filingDate"],
                "acceptanceDateTime": row["acceptanceDateTime"],
                "classification": classification,
                "reaction_session_date": reaction_session.isoformat(),
                "items": row["items"],
                "event_source": "SEC_EDGAR_8K_ITEM_2_02",
                "has_report_time_metadata": True,
                "has_earnings_surprise_magnitude": False,
                "tradable_direction_available": False,
            }
        )
    return pd.DataFrame(rows)


def validate_pead_sec_event_source_gate(gate_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(gate_dir)
    checks: list[dict[str, Any]] = []
    panel_path = path / "pead_sec_event_source_panel.csv"
    manifest_path = path / "event_source_manifest.json"
    decision_path = path / "final_decision.json"
    _check(checks, "panel_exists", panel_path.is_file(), str(panel_path))
    _check(checks, "manifest_exists", manifest_path.is_file(), str(manifest_path))
    _check(checks, "decision_exists", decision_path.is_file(), str(decision_path))
    if not panel_path.is_file() or not manifest_path.is_file() or not decision_path.is_file():
        return _report(checks)
    panel = pd.read_csv(panel_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    _check(checks, "has_events", len(panel) > 0, f"events={len(panel)}")
    _check(checks, "all_events_have_report_time", panel["has_report_time_metadata"].astype(bool).all(), "report-time metadata")
    _check(checks, "surprise_magnitude_missing", not panel["has_earnings_surprise_magnitude"].astype(bool).any(), "surprise absent")
    _check(checks, "direction_unavailable", not panel["tradable_direction_available"].astype(bool).any(), "direction absent")
    _check(checks, "manifest_blocked_on_surprise", manifest.get("status") == "blocked", str(manifest.get("status")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "decision_blocked", decision.get("decision") == "BLOCKED_EARNINGS_SURPRISE_MAGNITUDE_UNAVAILABLE", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PEAD SEC event-source gate.")
    parser.add_argument("--summary-path", default=str(SEC_SUMMARY))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_pead_sec_event_source_gate(args.summary_path)
    report = validate_pead_sec_event_source_gate()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _reaction_session_date(acceptance_utc: pd.Timestamp, classification: str) -> date:
    local = acceptance_utc.tz_convert(NY)
    if classification == "AMC":
        return _next_weekday(local.date())
    return local.date()


def _next_weekday(day: date) -> date:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _write_manifest(events: pd.DataFrame) -> dict[str, Any]:
    manifest = {
        "status": "blocked",
        "decision": "PEAD_SEC_EVENT_SOURCE_TIMESTAMP_PASS_SURPRISE_BLOCKED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "event_source": "SEC_EDGAR_8K_ITEM_2_02",
        "events_with_report_time": int(events["has_report_time_metadata"].sum()) if not events.empty else 0,
        "events_with_surprise_magnitude": int(events["has_earnings_surprise_magnitude"].sum()) if not events.empty else 0,
        "tradable_direction_events": int(events["tradable_direction_available"].sum()) if not events.empty else 0,
        "provider_query_performed_now": False,
        "backtest_authorized": False,
        "blocker": "SEC EDGAR provides official earnings report-time metadata but not earnings surprise magnitude or tradable direction.",
    }
    _write_json(ARTIFACT_DIR / "event_source_manifest.json", manifest)
    _write_csv(
        ARTIFACT_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["infer_direction_from_future_returns", "blocked", "Would be direct look-ahead leakage."],
            ["use_price_gap_as_surprise_proxy", "blocked", "Daily/intraday gap proxy is not an earnings surprise measure."],
            ["run_pead_backtest", "blocked", "No ex-ante earnings surprise or magnitude variable."],
            ["strategy_promotion", "blocked", "No backtest and no DSR."],
        ],
    )
    return manifest


def _write_decision(manifest: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "blocked",
        "decision": "BLOCKED_EARNINGS_SURPRISE_MAGNITUDE_UNAVAILABLE",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "events_with_report_time": manifest["events_with_report_time"],
        "events_with_surprise_magnitude": manifest["events_with_surprise_magnitude"],
        "tradable_direction_events": manifest["tradable_direction_events"],
        "provider_query_performed_now": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Add a point-in-time earnings surprise or event-magnitude source; do not infer direction from returns.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any]) -> str:
    return (
        "# Report PEAD SEC Event-Source Gate - 2026-05-21\n\n"
        f"Decision: {decision['decision']}\n\n"
        f"- Events with report-time metadata: {decision['events_with_report_time']}\n"
        f"- Events with earnings surprise magnitude: {decision['events_with_surprise_magnitude']}\n"
        f"- Tradable direction events: {decision['tradable_direction_events']}\n"
        "- Provider query performed now: false\n"
        "- Backtest performed: false\n\n"
        "Interpretation: SEC EDGAR solves the report-time problem but not the signal-direction problem. "
        "A PEAD backtest remains blocked until a point-in-time surprise or magnitude source is available.\n"
    )


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "PEAD_SEC_EVENT_SOURCE_GATE_PASS_BLOCKED_CLOSED" if failed == 0 else "PEAD_SEC_EVENT_SOURCE_GATE_FAIL",
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
