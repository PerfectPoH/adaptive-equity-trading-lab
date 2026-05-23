from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.experiments.pead_earnings_source_probe_gate_validator import validate_pead_earnings_source_probe_gate


RUN_ID = "PROBE-PEAD-EARNINGS-SOURCE-001"
SPEC_DIR = Path("experiments/provider_aware_research/pead_earnings_source_probe_gate_20260523")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/PROBE-PEAD-EARNINGS-SOURCE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-Earnings-Source-Probe-2026-05-23.md")
INTRINIO_BASE_URL = "https://api-v2.intrinio.com"


FIELD_GROUPS = {
    "earnings_date": {"expected_date", "date", "earnings_date", "report_date"},
    "timing": {"expected_8k_at", "report_time", "time_of_day", "confirmed_time", "timestamp"},
    "actual_eps": {"actual_eps", "reported_eps", "eps_actual", "actual", "earnings_per_share"},
    "consensus_eps": {"consensus_eps", "estimate_eps", "estimated_eps", "mean_estimate", "analyst_estimate", "consensus"},
    "pit_metadata": {"updated_at", "created_at", "revised_at", "as_of_date", "expected_8k_at"},
}


def run_pead_earnings_source_probe(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_pead_earnings_source_probe_gate(spec_dir)
    _write_json(output / "pre_query_gate_validation_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked("BLOCKED_EARNINGS_SOURCE_GATE_FAILED", provider_query=False, reason="gate_failed")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision
    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    api_key = _load_intrinio_api_key()
    if not api_key:
        decision = _blocked("BLOCKED_EARNINGS_SOURCE_API_KEY_MISSING", provider_query=False, reason="INTRINIO_API_KEY missing")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision
    try:
        payload = _fetch_json(_intrinio_url(manifest, api_key))
    except HTTPError as exc:
        decision = _blocked("BLOCKED_EARNINGS_SOURCE_PROVIDER_ERROR", provider_query=True, reason=f"HTTP_ERROR_{exc.code}:{exc.reason}")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision
    except URLError as exc:
        decision = _blocked("BLOCKED_EARNINGS_SOURCE_PROVIDER_ERROR", provider_query=True, reason=f"URL_ERROR:{exc.reason}")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision

    summary = summarize_payload_fields(payload)
    decision = build_source_decision(summary)
    _write_outputs(output, Path(vault_report), decision, summary)
    return decision


def summarize_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    records = _records(payload)
    first = records[0] if records else {}
    keys = set(first.keys())
    present = {group: sorted(keys & accepted) for group, accepted in FIELD_GROUPS.items()}
    missing = [f"{group}_missing" for group, matches in present.items() if not matches]
    return {
        "run_id": RUN_ID,
        "status": "complete",
        "payload_top_level_keys": sorted(payload.keys()),
        "record_count": len(records),
        "first_record_keys": sorted(keys),
        "field_group_matches": present,
        "missing_requirements": missing,
        "raw_payload_retained": False,
        "provider_query_performed": True,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def build_source_decision(summary: dict[str, Any]) -> dict[str, Any]:
    blockers = list(summary["missing_requirements"])
    decision = "PEAD_SOURCE_CANDIDATE" if not blockers else "BLOCKED_EARNINGS_SOURCE_INSUFFICIENT"
    return {
        "status": "complete",
        "decision": decision,
        "run_id": RUN_ID,
        "provider": "Intrinio",
        "symbol": "CRMD",
        "record_count": summary["record_count"],
        "blockers": blockers,
        "provider_query_performed": True,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "promotion_allowed": False,
    }


def _blocked(decision: str, *, provider_query: bool, reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": decision,
        "run_id": RUN_ID,
        "provider": "Intrinio",
        "symbol": "CRMD",
        "reason": reason,
        "blockers": [reason],
        "provider_query_performed": provider_query,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "promotion_allowed": False,
    }


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("expected_earnings", "upcoming_earnings", "earnings", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _intrinio_url(manifest: dict[str, Any], api_key: str) -> str:
    query = urlencode(
        {
            "expected_date_after": manifest["expected_date_after"],
            "expected_date_before": manifest["expected_date_before"],
            "page_size": 10,
            "api_key": api_key,
        }
    )
    return f"{INTRINIO_BASE_URL}/companies/{manifest['symbol']}/upcoming_earnings?{query}"


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-pead-source-probe"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_intrinio_api_key() -> str:
    key = os.environ.get("INTRINIO_API_KEY", "").strip()
    if key:
        return key
    env_path = Path(".env")
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("INTRINIO_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _write_outputs(output: Path, vault_report: Path, decision: dict[str, Any], summary: dict[str, Any]) -> None:
    _write_json(output / "final_decision.json", decision)
    _write_json(output / "source_field_summary.json", summary or {"status": "not_available", "raw_payload_retained": False})
    text = (
        "# Report PEAD Earnings Source Probe - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single bounded provider-source probe. No market data download, backtest, paper/live trading, or promotion occurred. Raw payload was not retained.\n\n"
        "## Result\n\n"
        f"- Provider query performed: {decision['provider_query_performed']}\n"
        f"- Record count: {decision.get('record_count', 0)}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n"
    )
    vault_report.parent.mkdir(parents=True, exist_ok=True)
    vault_report.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_only:
        report = validate_pead_earnings_source_probe_gate(SPEC_DIR)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_pead_earnings_source_probe()
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] in {"complete", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
