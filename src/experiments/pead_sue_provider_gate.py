from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any


TRIAL_ID = "TRIAL-PEAD-EARNINGS-001"
RUN_ID = "PEAD-SUE-PROVIDER-GATE-001"
ROOT = Path("experiments/provider_aware_research")
ARTIFACT_DIR = ROOT / "pead_sue_provider_gate_20260521"
INTRINIO_EARNINGS_PROBE = ROOT / "execution_outputs" / "XMOM-EARNINGS-SINGLE-PROBE-001" / "single_probe_execution_manifest.json"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-SUE-Provider-Gate-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-pead-sue-provider-gate.md")


def run_pead_sue_provider_gate() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = build_sue_provider_candidates()
    _write_csv(ARTIFACT_DIR / "sue_provider_candidates.csv", list(candidates[0].keys()), [[row[key] for key in row] for row in candidates])
    credential = inspect_sue_credentials()
    _write_json(ARTIFACT_DIR / "credential_review.json", credential)
    manifest = _write_manifest(candidates, credential)
    decision = _write_decision(manifest)
    return decision


def build_sue_provider_candidates() -> list[dict[str, Any]]:
    return [
        {
            "provider": "Intrinio Zacks EPS Surprises",
            "role": "primary_candidate_if_entitled",
            "evidence": "Official Intrinio endpoint documents Zacks EPS surprise records with estimated and actual earnings.",
            "source_url": "https://data.intrinio.com/documentation/web_api/get_zacks_eps_surprises_v2",
            "required_fields": "actual_eps; estimated_eps; surprise; fiscal_period; report_date",
            "point_in_time_risk": "entitlement_and_vendor_timestamp_must_be_verified",
            "current_status": "blocked_prior_intrinio_earnings_probe_403",
        },
        {
            "provider": "Nasdaq Data Link / Zacks dataset",
            "role": "secondary_candidate_if_subscription_exists",
            "evidence": "Nasdaq Data Link supports premium datasets through API; Zacks surprise datasets are a known paid route.",
            "source_url": "https://docs.data.nasdaq.com/docs/getting-started",
            "required_fields": "actual_eps; consensus_eps; surprise_percent; report_date",
            "point_in_time_risk": "subscription_and_dataset_schema_must_be_confirmed",
            "current_status": "blocked_no_api_key_or_subscription_detected",
        },
        {
            "provider": "Estimize",
            "role": "alternative_consensus_candidate",
            "evidence": "Estimize documentation exposes EPS and consensus EPS estimates.",
            "source_url": "https://s3.amazonaws.com/com.estimize.public/EstimizeAPI.pdf",
            "required_fields": "eps; consensus_eps_estimate; release_date",
            "point_in_time_risk": "coverage_bias_and_api_access_must_be_confirmed",
            "current_status": "blocked_no_api_key_detected",
        },
    ]


def inspect_sue_credentials() -> dict[str, Any]:
    env_text = Path(".env").read_text(encoding="utf-8") if Path(".env").exists() else ""
    prior_intrinio = {}
    if INTRINIO_EARNINGS_PROBE.exists():
        prior_intrinio = json.loads(INTRINIO_EARNINGS_PROBE.read_text(encoding="utf-8"))
    return {
        "status": "blocked",
        "intrinio_api_key_present": _has_key("INTRINIO_API_KEY", env_text),
        "intrinio_prior_earnings_probe_error": prior_intrinio.get("error", "missing_prior_probe"),
        "nasdaq_data_link_api_key_present": _has_key("NASDAQ_DATA_LINK_API_KEY", env_text) or _has_key("QUANDL_API_KEY", env_text),
        "estimize_api_key_present": _has_key("ESTIMIZE_API_KEY", env_text),
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "conclusion": "No validated PIT SUE provider entitlement is available for execution.",
    }


def validate_pead_sue_provider_gate(gate_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(gate_dir)
    checks: list[dict[str, Any]] = []
    required = ["sue_provider_candidates.csv", "credential_review.json", "sue_provider_gate_manifest.json", "final_decision.json", "blocked_actions.csv"]
    _check(checks, "gate_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if not all(check["status"] == "pass" for check in checks):
        return _report(checks)
    candidates = _read_csv(path / "sue_provider_candidates.csv")
    credential = json.loads((path / "credential_review.json").read_text(encoding="utf-8"))
    manifest = json.loads((path / "sue_provider_gate_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    _check(checks, "has_three_candidates", len(candidates) >= 3, f"candidates={len(candidates)}")
    _check(checks, "all_candidates_blocked", all(str(row["current_status"]).startswith("blocked") for row in candidates), "blocked candidates")
    _check(checks, "no_query_now", credential.get("provider_query_performed_now") is False, str(credential.get("provider_query_performed_now")))
    _check(checks, "manifest_blocked", manifest.get("status") == "blocked", str(manifest.get("status")))
    _check(checks, "decision_blocks_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "decision_sue_unavailable", decision.get("decision") == "BLOCKED_PIT_SUE_PROVIDER_UNAVAILABLE", str(decision.get("decision")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PEAD SUE provider gate.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_pead_sue_provider_gate()
    report = validate_pead_sue_provider_gate()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _write_manifest(candidates: list[dict[str, Any]], credential: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "status": "blocked",
        "decision": "PEAD_SUE_PROVIDER_GATE_BLOCKED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "candidate_count": len(candidates),
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "pit_sue_provider_available": False,
        "backtest_authorized": False,
        "blocker": "No validated point-in-time SUE/consensus provider entitlement is available.",
        "credential_review": credential,
    }
    _write_json(ARTIFACT_DIR / "sue_provider_gate_manifest.json", manifest)
    _write_csv(
        ARTIFACT_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            ["query_unentitled_provider", "blocked", "No endpoint guessing or repeated 403 loops."],
            ["scrape_zacks_pages", "blocked", "Scraping pages would not guarantee PIT entitlement or stable schema."],
            ["infer_surprise_from_returns", "blocked", "Future-return direction is leakage."],
            ["run_pead_backtest", "blocked", "No PIT SUE provider available."],
            ["strategy_promotion", "blocked", "No backtest and no DSR."],
        ],
    )
    return manifest


def _write_decision(manifest: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "blocked",
        "decision": "BLOCKED_PIT_SUE_PROVIDER_UNAVAILABLE",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "pit_sue_provider_available": False,
        "provider_query_performed_now": False,
        "network_call_performed_now": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Obtain/verify one PIT SUE provider entitlement, then run a single approved provider probe for CRMD.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    text = _format_report(decision, manifest)
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")
    return decision


def _format_report(decision: dict[str, Any], manifest: dict[str, Any]) -> str:
    cred = manifest["credential_review"]
    return (
        "# Report PEAD SUE Provider Gate - 2026-05-21\n\n"
        f"Decision: {decision['decision']}\n\n"
        "## Credential Review\n"
        f"- Intrinio key present: {cred['intrinio_api_key_present']}\n"
        f"- Prior Intrinio earnings probe error: {cred['intrinio_prior_earnings_probe_error']}\n"
        f"- Nasdaq Data Link key present: {cred['nasdaq_data_link_api_key_present']}\n"
        f"- Estimize key present: {cred['estimize_api_key_present']}\n"
        "- Provider query performed now: false\n"
        "- Backtest performed: false\n\n"
        "## Interpretation\n"
        "The scientifically preferred PEAD path is SUE/consensus, but the lab has no validated point-in-time SUE provider entitlement. "
        "PEAD remains blocked rather than being approximated with returns, gaps, or scraped pages.\n"
    )


def _has_key(key: str, env_text: str) -> bool:
    return bool(os.environ.get(key, "").strip()) or f"{key}=" in env_text


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "PEAD_SUE_PROVIDER_GATE_PASS_BLOCKED_CLOSED" if failed == 0 else "PEAD_SUE_PROVIDER_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
