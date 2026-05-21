from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path
from typing import Any

from src.validation.earnings_timestamp_classifier import classify_earnings_timestamp


TRIAL_ID = "TRIAL-PEAD-EARNINGS-001"
RUN_ID = "SEC-EDGAR-EARNINGS-PROVIDER-PROBE-001"
ROOT = Path("experiments/provider_aware_research")
ARTIFACT_DIR = ROOT / "sec_edgar_earnings_provider_probe_20260521"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC-EDGAR-Earnings-Provider-Probe-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-sec-edgar-earnings-provider-probe.md")
SEC_UA = "adaptive-equity-trading-lab research-contact@example.com"


def run_sec_edgar_earnings_provider_probe(symbol: str = "CRMD") -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    ticker = _fetch_json("https://www.sec.gov/files/company_tickers.json")
    match = _find_ticker(ticker, symbol)
    if match is None:
        return _write_blocked("symbol_not_found_in_sec_company_tickers", symbol=symbol)
    cik = f"{int(match['cik_str']):010d}"
    submissions = _fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    records = _extract_recent_earnings_8k_records(submissions)
    summary_rows = [_summarize_record(record) for record in records[:10]]
    _write_csv(
        ARTIFACT_DIR / "sec_edgar_earnings_8k_summary.csv",
        ["accessionNumber", "filingDate", "acceptanceDateTime", "items", "classification", "action", "reaction_session"],
        [[row.get(col, "") for col in ["accessionNumber", "filingDate", "acceptanceDateTime", "items", "classification", "action", "reaction_session"]] for row in summary_rows],
    )
    classifiable = [row for row in summary_rows if row["classification"] in {"BMO", "AMC", "DMT"}]
    candidates = [row for row in summary_rows if row["classification"] in {"BMO", "AMC"}]
    manifest = {
        "status": "pass" if candidates else "blocked",
        "decision": "SEC_EDGAR_EARNINGS_PROVIDER_METADATA_PASS" if candidates else "SEC_EDGAR_EARNINGS_PROVIDER_METADATA_BLOCKED",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "provider": "SEC EDGAR submissions API",
        "symbol": symbol,
        "cik": cik,
        "provider_query_performed": True,
        "network_call_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "earnings_8k_records_found": len(records),
        "timestamp_classifiable_records": len(classifiable),
        "bmo_amc_candidate_records": len(candidates),
        "first_candidate": candidates[0] if candidates else None,
    }
    _write_json(ARTIFACT_DIR / "sec_edgar_provider_probe_manifest.json", manifest)
    _write_report(manifest)
    return manifest


def validate_sec_edgar_earnings_provider_probe(probe_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(probe_dir)
    checks: list[dict[str, Any]] = []
    manifest_path = path / "sec_edgar_provider_probe_manifest.json"
    summary_path = path / "sec_edgar_earnings_8k_summary.csv"
    _check(checks, "manifest_exists", manifest_path.is_file(), str(manifest_path))
    _check(checks, "summary_exists", summary_path.is_file(), str(summary_path))
    if not manifest_path.is_file() or not summary_path.is_file():
        return _report(checks)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _check(checks, "probe_passed", manifest.get("status") == "pass", str(manifest.get("status")))
    _check(checks, "sec_provider", manifest.get("provider") == "SEC EDGAR submissions API", str(manifest.get("provider")))
    _check(checks, "raw_payload_not_retained", manifest.get("raw_payload_retained") is False, str(manifest.get("raw_payload_retained")))
    _check(checks, "has_bmo_or_amc_candidates", int(manifest.get("bmo_amc_candidate_records", 0)) > 0, str(manifest.get("bmo_amc_candidate_records")))
    _check(checks, "no_backtest", manifest.get("backtest_performed") is False, str(manifest.get("backtest_performed")))
    return _report(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe SEC EDGAR as earnings report-time metadata provider.")
    parser.add_argument("--symbol", default="CRMD")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_sec_edgar_earnings_provider_probe(args.symbol)
    report = validate_sec_edgar_earnings_provider_probe()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": SEC_UA, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_ticker(payload: dict[str, Any], symbol: str) -> dict[str, Any] | None:
    upper = symbol.upper()
    for value in payload.values():
        if str(value.get("ticker", "")).upper() == upper:
            return value
    return None


def _extract_recent_earnings_8k_records(submissions: dict[str, Any]) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    rows = []
    for idx, form in enumerate(forms):
        items = _get_recent_value(recent, "items", idx)
        if form != "8-K" or "2.02" not in str(items):
            continue
        rows.append(
            {
                "accessionNumber": _get_recent_value(recent, "accessionNumber", idx),
                "filingDate": _get_recent_value(recent, "filingDate", idx),
                "acceptanceDateTime": _get_recent_value(recent, "acceptanceDateTime", idx),
                "items": items,
            }
        )
    return rows


def _summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    classification = classify_earnings_timestamp(str(record.get("acceptanceDateTime", "")))
    return {
        **record,
        "classification": classification.classification,
        "action": classification.action,
        "reaction_session": classification.reaction_session or "",
    }


def _get_recent_value(recent: dict[str, list[Any]], key: str, idx: int) -> Any:
    values = recent.get(key, [])
    if idx >= len(values):
        return ""
    return values[idx]


def _write_blocked(reason: str, **extra: Any) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "blocked",
        "decision": "SEC_EDGAR_EARNINGS_PROVIDER_METADATA_BLOCKED",
        "reason": reason,
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "provider_query_performed": True,
        "raw_payload_retained": False,
        **extra,
    }
    _write_json(ARTIFACT_DIR / "sec_edgar_provider_probe_manifest.json", manifest)
    return manifest


def _write_report(manifest: dict[str, Any]) -> None:
    text = (
        "# Report SEC EDGAR Earnings Provider Probe - 2026-05-21\n\n"
        f"Decision: {manifest['decision']}\n\n"
        f"- Provider: {manifest['provider']}\n"
        f"- Symbol/CIK: {manifest['symbol']} / {manifest['cik']}\n"
        f"- Earnings 8-K Item 2.02 records found: {manifest['earnings_8k_records_found']}\n"
        f"- BMO/AMC candidate records: {manifest['bmo_amc_candidate_records']}\n"
        "- Raw payload retained: false\n"
        "- Backtest performed: false\n\n"
        "Interpretation: SEC EDGAR can supply official filing acceptance timestamps for earnings-related 8-K Item 2.02 events. "
        "This resolves the metadata-provider direction for the next PEAD gate, but does not yet authorize a PEAD backtest.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


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
        "gate_decision": "SEC_EDGAR_EARNINGS_PROVIDER_PROBE_PASS" if failed == 0 else "SEC_EDGAR_EARNINGS_PROVIDER_PROBE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
