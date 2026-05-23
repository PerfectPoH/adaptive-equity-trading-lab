from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.experiments.pead_alphavantage_earnings_probe_gate_validator import validate_pead_alphavantage_earnings_probe_gate


RUN_ID = "PROBE-PEAD-ALPHAVANTAGE-EARNINGS-001"
SPEC_DIR = Path("experiments/provider_aware_research/pead_alphavantage_earnings_probe_gate_20260523")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/PROBE-PEAD-ALPHAVANTAGE-EARNINGS-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-PEAD-AlphaVantage-Earnings-Probe-2026-05-23.md")
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"


FIELD_GROUPS = {
    "earnings_date": {"reportedDate", "fiscalDateEnding", "reported_date", "fiscal_date_ending"},
    "actual_eps": {"reportedEPS", "actualEPS", "reported_eps"},
    "consensus_eps": {"estimatedEPS", "estimateEPS", "consensusEPS", "estimated_eps"},
    "surprise": {"surprise", "surprisePercentage", "surprise_percentage"},
    "timing": {"reportTime", "timeOfDay", "bmo_amc", "confirmedTime", "timestamp"},
    "pit_metadata": {"updated_at", "created_at", "revised_at", "as_of_date", "lastRefreshed", "asOfDate"},
}


def run_pead_alphavantage_earnings_probe(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_pead_alphavantage_earnings_probe_gate(spec_dir)
    _write_json(output / "pre_query_gate_validation_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked("BLOCKED_ALPHAVANTAGE_GATE_FAILED", provider_query=False, reason="gate_failed")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision

    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    api_key = _load_alphavantage_api_key()
    if not api_key:
        decision = _blocked("BLOCKED_ALPHAVANTAGE_API_KEY_MISSING", provider_query=False, reason="ALPHAVANTAGE_API_KEY missing")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision

    try:
        payload = _fetch_json(_alphavantage_url(manifest, api_key))
    except HTTPError as exc:
        decision = _blocked("BLOCKED_ALPHAVANTAGE_PROVIDER_ERROR", provider_query=True, reason=f"HTTP_ERROR_{exc.code}:{exc.reason}")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision
    except URLError as exc:
        decision = _blocked("BLOCKED_ALPHAVANTAGE_PROVIDER_ERROR", provider_query=True, reason=f"URL_ERROR:{exc.reason}")
        _write_outputs(output, Path(vault_report), decision, {})
        return decision

    provider_error = _provider_error(payload)
    if provider_error:
        decision = _blocked("BLOCKED_ALPHAVANTAGE_PROVIDER_ERROR", provider_query=True, reason=provider_error)
        _write_outputs(output, Path(vault_report), decision, summarize_payload_fields(payload))
        return decision

    summary = summarize_payload_fields(payload)
    decision = build_source_decision(summary)
    _write_outputs(output, Path(vault_report), decision, summary)
    return decision


def summarize_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    records = _records(payload)
    first = records[0] if records else {}
    top_level_keys = set(payload.keys())
    record_keys = set(first.keys())
    combined_keys = top_level_keys | record_keys
    present = {group: sorted(combined_keys & accepted) for group, accepted in FIELD_GROUPS.items()}
    missing = [f"{group}_missing" for group, matches in present.items() if not matches]
    return {
        "run_id": RUN_ID,
        "status": "complete",
        "payload_top_level_keys": sorted(top_level_keys),
        "record_count": len(records),
        "first_record_keys": sorted(record_keys),
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
    decision = "PEAD_ALPHAVANTAGE_SOURCE_CANDIDATE" if not blockers else "BLOCKED_ALPHAVANTAGE_SOURCE_INSUFFICIENT"
    return {
        "status": "complete",
        "decision": decision,
        "run_id": RUN_ID,
        "provider": "Alpha Vantage",
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
        "provider": "Alpha Vantage",
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
    for key in ("quarterlyEarnings", "annualEarnings", "earnings", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _provider_error(payload: dict[str, Any]) -> str:
    for key in ("Error Message", "Information", "Note"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return f"{key}: {value.strip()[:160]}"
    return ""


def _alphavantage_url(manifest: dict[str, Any], api_key: str) -> str:
    query = urlencode({"function": manifest["function"], "symbol": manifest["symbol"], "apikey": api_key})
    return f"{ALPHAVANTAGE_BASE_URL}?{query}"


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-pead-alphavantage-probe"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_alphavantage_api_key() -> str:
    key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if key:
        return key
    env_path = Path(".env")
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ALPHAVANTAGE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _write_outputs(output: Path, vault_report: Path, decision: dict[str, Any], summary: dict[str, Any]) -> None:
    _write_json(output / "final_decision.json", decision)
    _write_json(output / "source_field_summary.json", summary or {"status": "not_available", "raw_payload_retained": False})
    text = (
        "# Report PEAD Alpha Vantage Earnings Probe - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single bounded Alpha Vantage EARNINGS source probe. No market data download, backtest, parameter sweep, paper/live trading, or promotion occurred. Raw payload was not retained.\n\n"
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
        report = validate_pead_alphavantage_earnings_probe_gate(SPEC_DIR)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_pead_alphavantage_earnings_probe()
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] in {"complete", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
