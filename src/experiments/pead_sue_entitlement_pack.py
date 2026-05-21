from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


TRIAL_ID = "TRIAL-PEAD-EARNINGS-001"
RUN_ID = "PEAD-SUE-ENTITLEMENT-PACK-001"
ROOT = Path("experiments/provider_aware_research")
ARTIFACT_DIR = ROOT / "pead_sue_entitlement_pack_20260521"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-SUE-Entitlement-Pack-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-pead-sue-entitlement-pack.md")


def run_pead_sue_entitlement_pack() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    questions = build_provider_questions()
    acceptance = build_acceptance_criteria()
    probe = build_one_call_probe_spec()
    blocked = build_blocked_actions()
    _write_csv(ARTIFACT_DIR / "provider_entitlement_questions.csv", list(questions[0].keys()), questions)
    _write_csv(ARTIFACT_DIR / "acceptance_criteria.csv", list(acceptance[0].keys()), acceptance)
    _write_json(ARTIFACT_DIR / "one_call_probe_spec.json", probe)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", list(blocked[0].keys()), blocked)
    manifest = _write_manifest(questions, acceptance, probe)
    decision = _write_decision(manifest)
    return decision


def build_provider_questions() -> list[dict[str, Any]]:
    return [
        {
            "question_id": "PIT_SUE_001",
            "topic": "point_in_time_availability",
            "question": "Can EPS consensus, actual EPS, surprise value, and surprise percent be queried as they were known before the reaction session?",
            "required_answer": "yes_with_asof_or_auditable_pre_release_timestamp",
            "failure_mode": "posthoc_consensus_or_latest_only_values",
        },
        {
            "question_id": "PIT_SUE_002",
            "topic": "field_schema",
            "question": "Does the endpoint expose symbol/identifier, fiscal period, report date, actual EPS, consensus EPS, surprise, and surprise percent in stable fields?",
            "required_answer": "all_required_fields_present",
            "failure_mode": "missing_consensus_or_surprise_magnitude",
        },
        {
            "question_id": "PIT_SUE_003",
            "topic": "timestamp_alignment",
            "question": "Does the provider expose report timestamp metadata, or can its report date be deterministically joined to SEC EDGAR Item 2.02 acceptanceDateTime?",
            "required_answer": "timestamp_present_or_sec_join_allowed",
            "failure_mode": "date_only_without_sec_join",
        },
        {
            "question_id": "PIT_SUE_004",
            "topic": "coverage_bias",
            "question": "Does historical coverage include inactive, delisted, acquired, and low-liquidity small-cap issuers, or is coverage limited to current survivors?",
            "required_answer": "coverage_policy_disclosed_and_delisted_supported_or_measured",
            "failure_mode": "survivorship_biased_current_universe_only",
        },
        {
            "question_id": "PIT_SUE_005",
            "topic": "revision_policy",
            "question": "Are estimate revisions and late corrections versioned, or does the endpoint overwrite history with restated values?",
            "required_answer": "revision_policy_disclosed",
            "failure_mode": "silent_history_rewrites",
        },
        {
            "question_id": "PIT_SUE_006",
            "topic": "license_and_retention",
            "question": "Can derived fields and redacted probe summaries be retained in the research repository without storing raw licensed payloads?",
            "required_answer": "derived_retention_allowed_raw_retention_not_required",
            "failure_mode": "license_forbids_auditable_artifacts",
        },
    ]


def build_acceptance_criteria() -> list[dict[str, Any]]:
    return [
        {
            "criterion_id": "ACCEPT_001",
            "requirement": "single_probe_scope",
            "pass_condition": "Exactly one provider, one symbol, one endpoint, one network call, and no raw payload retention.",
            "blocking_if_failed": True,
        },
        {
            "criterion_id": "ACCEPT_002",
            "requirement": "sue_schema",
            "pass_condition": "Probe summary contains actual EPS, consensus or estimated EPS, surprise magnitude, surprise percent or computable equivalent, fiscal period, and report date.",
            "blocking_if_failed": True,
        },
        {
            "criterion_id": "ACCEPT_003",
            "requirement": "point_in_time_claim",
            "pass_condition": "Provider documentation or response metadata supports point-in-time use, as-of query semantics, or an auditable pre-release estimate snapshot.",
            "blocking_if_failed": True,
        },
        {
            "criterion_id": "ACCEPT_004",
            "requirement": "sec_join_compatibility",
            "pass_condition": "Provider record can be joined to SEC EDGAR Item 2.02 event by symbol/CIK plus fiscal period/report date without using returns.",
            "blocking_if_failed": True,
        },
        {
            "criterion_id": "ACCEPT_005",
            "requirement": "no_strategy_execution",
            "pass_condition": "The provider probe produces only entitlement/schema evidence; no extractor, PEAD backtest, parameter sweep, paper trade, live trade, or promotion is executed.",
            "blocking_if_failed": True,
        },
    ]


def build_one_call_probe_spec() -> dict[str, Any]:
    return {
        "status": "approved_template_not_executable",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "candidate_symbol": "CRMD",
        "candidate_provider_priority": [
            "Intrinio Zacks EPS Surprises if entitlement is verified",
            "Nasdaq Data Link / Zacks if subscription and schema are verified",
            "Estimize if API access and coverage policy are verified",
        ],
        "max_provider_calls": 1,
        "raw_payload_retention": False,
        "network_call_authorized_now": False,
        "backtest_authorized": False,
        "required_output_fields": [
            "provider",
            "endpoint",
            "symbol",
            "fiscal_period",
            "report_date",
            "actual_eps",
            "consensus_eps_or_estimated_eps",
            "surprise_magnitude",
            "surprise_percent_or_computable_equivalent",
            "point_in_time_evidence",
            "sec_edgar_join_key",
        ],
        "success_decision": "SUE_PROVIDER_ENTITLEMENT_VERIFIED_FOR_SINGLE_PROBE_ONLY",
        "failure_decision": "BLOCKED_PIT_SUE_PROVIDER_UNAVAILABLE",
    }


def build_blocked_actions() -> list[dict[str, Any]]:
    return [
        {
            "action": "query_provider_without_entitlement_answer",
            "status": "blocked",
            "reason": "The current step is a pre-query entitlement pack, not execution.",
        },
        {
            "action": "infer_sue_from_price_reaction",
            "status": "blocked",
            "reason": "Using post-event returns to infer earnings surprise is direct label leakage.",
        },
        {
            "action": "scrape_unversioned_web_pages",
            "status": "blocked",
            "reason": "Unversioned pages do not provide PIT consensus or auditable revision policy.",
        },
        {
            "action": "run_pead_backtest",
            "status": "blocked",
            "reason": "No validated PIT SUE provider has passed the one-call probe.",
        },
        {
            "action": "promote_strategy",
            "status": "blocked",
            "reason": "No PEAD signal, no backtest, no CPCV/DSR result.",
        },
    ]


def validate_pead_sue_entitlement_pack(pack_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(pack_dir)
    checks: list[dict[str, Any]] = []
    required = [
        "provider_entitlement_questions.csv",
        "acceptance_criteria.csv",
        "one_call_probe_spec.json",
        "entitlement_pack_manifest.json",
        "blocked_actions.csv",
        "final_decision.json",
    ]
    _check(checks, "pack_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)

    questions = _read_csv(path / "provider_entitlement_questions.csv")
    acceptance = _read_csv(path / "acceptance_criteria.csv")
    probe = json.loads((path / "one_call_probe_spec.json").read_text(encoding="utf-8"))
    manifest = json.loads((path / "entitlement_pack_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv(path / "blocked_actions.csv")
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))

    _check(checks, "has_minimum_provider_questions", len(questions) >= 6, f"questions={len(questions)}")
    _check(checks, "questions_cover_pit", any(row["topic"] == "point_in_time_availability" for row in questions), "PIT topic")
    _check(checks, "questions_cover_revision_policy", any(row["topic"] == "revision_policy" for row in questions), "revision topic")
    _check(checks, "all_acceptance_criteria_blocking", all(str(row["blocking_if_failed"]).lower() == "true" for row in acceptance), "blocking criteria")
    _check(checks, "single_call_limit", probe.get("max_provider_calls") == 1, str(probe.get("max_provider_calls")))
    _check(checks, "raw_payload_retention_disabled", probe.get("raw_payload_retention") is False, str(probe.get("raw_payload_retention")))
    _check(checks, "network_call_not_authorized", probe.get("network_call_authorized_now") is False, str(probe.get("network_call_authorized_now")))
    required_fields = set(probe.get("required_output_fields", []))
    _check(checks, "requires_sue_fields", {"actual_eps", "consensus_eps_or_estimated_eps", "surprise_magnitude"}.issubset(required_fields), str(required_fields))
    _check(checks, "manifest_not_executable", manifest.get("status") == "ready_not_executable", str(manifest.get("status")))
    _check(checks, "blocks_price_reaction_sue", any(row["action"] == "infer_sue_from_price_reaction" and row["status"] == "blocked" for row in blocked), "price proxy blocked")
    _check(checks, "decision_not_backtested", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "decision_waits_for_provider", decision.get("decision") == "READY_FOR_SUE_PROVIDER_ENTITLEMENT_VERIFICATION", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PEAD SUE provider entitlement pack.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_pead_sue_entitlement_pack()
    report = validate_pead_sue_entitlement_pack()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _write_manifest(questions: list[dict[str, Any]], acceptance: list[dict[str, Any]], probe: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "status": "ready_not_executable",
        "decision": "PEAD_SUE_ENTITLEMENT_PACK_READY",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "question_count": len(questions),
        "acceptance_criteria_count": len(acceptance),
        "max_provider_calls": probe["max_provider_calls"],
        "network_call_performed_now": False,
        "provider_query_performed_now": False,
        "raw_payload_retention": False,
        "backtest_authorized": False,
        "purpose": "Turn the PIT SUE provider blocker into a bounded entitlement verification workflow.",
    }
    _write_json(ARTIFACT_DIR / "entitlement_pack_manifest.json", manifest)
    return manifest


def _write_decision(manifest: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "ready_not_executable",
        "decision": "READY_FOR_SUE_PROVIDER_ENTITLEMENT_VERIFICATION",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Answer provider entitlement questions, then run exactly one approved SUE schema probe for CRMD if all acceptance criteria can be tested.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, manifest)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], manifest: dict[str, Any]) -> str:
    return (
        "# Report PEAD SUE Entitlement Pack - 2026-05-21\n\n"
        f"Decision: {decision['decision']}\n\n"
        "## Scope\n"
        "- Purpose: convert the PIT SUE provider blocker into a bounded verification workflow.\n"
        f"- Provider questions: {manifest['question_count']}\n"
        f"- Acceptance criteria: {manifest['acceptance_criteria_count']}\n"
        f"- Max provider calls in future probe: {manifest['max_provider_calls']}\n"
        "- Provider query performed now: false\n"
        "- Backtest performed: false\n\n"
        "## Interpretation\n"
        "PEAD remains scientifically blocked until a point-in-time SUE or consensus provider is verified. "
        "This pack defines the exact questions, pass/fail criteria, and one-call probe shape needed to unlock that gate without using returns, daily gaps, or scraped pages as proxies.\n"
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "PEAD_SUE_ENTITLEMENT_PACK_PASS_READY_NOT_EXECUTABLE" if failed == 0 else "PEAD_SUE_ENTITLEMENT_PACK_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
