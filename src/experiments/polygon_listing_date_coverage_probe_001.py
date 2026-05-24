from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_listing_date_coverage_probe_validator import (
    validate_polygon_listing_date_coverage_probe_gate,
)


RUN_ID = "POLYGON-LISTING-DATE-COVERAGE-PROBE-001"
TRIAL_ID = "UNIVERSE-LISTING-DATE-COVERAGE-PROBE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_listing_date_coverage_probe_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-LISTING-DATE-COVERAGE-PROBE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Listing-Date-Coverage-Probe-001-2026-05-24.md")
MIN_SUCCESS_COUNT = 8
MIN_LIST_DATE_COVERAGE = 0.80


def run_polygon_listing_date_coverage_probe_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_listing_date_coverage_probe_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED", provider_query=False, call_count=0)
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    tickers = _load_probe_tickers(manifest)
    api_key = _load_polygon_api_key()
    if not api_key:
        assessment = _empty_assessment(tickers, ["missing_polygon_api_key"], provider_query=False)
        decision = _blocked_decision("BLOCKED_POLYGON_API_KEY_MISSING", provider_query=False, call_count=0)
    else:
        payloads: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for ticker in tickers:
            try:
                payloads.append(_fetch_polygon_ticker_details(api_key, ticker=ticker))
            except Exception as exc:  # pragma: no cover - network/entitlement path
                errors.append({"ticker": ticker, "error": f"{type(exc).__name__}: {exc}"})
        assessment = assess_listing_date_coverage(payloads, expected_tickers=tickers)
        assessment["provider_errors"] = errors
        decision = _decision(assessment)
    rows = list(assessment.get("derived_listing_date_sample", []))
    _write_csv(output / "derived_listing_date_coverage_sample.csv", _fieldnames(rows), rows)
    _write_json(output / "listing_date_coverage_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_listing_date_coverage(payloads: list[dict[str, Any]], *, expected_tickers: list[str]) -> dict[str, Any]:
    derived = []
    seen = set()
    for payload in payloads:
        result = payload.get("results", {}) if isinstance(payload, dict) else {}
        if not isinstance(result, dict) or not result:
            continue
        row = _derived_row(result)
        if row["ticker"]:
            seen.add(row["ticker"])
        derived.append(row)
    detail_success_count = len(derived)
    list_date_present_count = sum(1 for row in derived if row["list_date"])
    expected_count = len(expected_tickers)
    coverage = list_date_present_count / expected_count if expected_count else 0.0
    missing_tickers = [ticker for ticker in expected_tickers if ticker not in seen]
    blockers: list[str] = []
    if detail_success_count < MIN_SUCCESS_COUNT:
        blockers.append("detail_success_count_below_8")
    if coverage < MIN_LIST_DATE_COVERAGE:
        blockers.append("list_date_coverage_below_0_80")
    passed = not blockers
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "expected_tickers": expected_tickers,
        "expected_ticker_count": expected_count,
        "detail_success_count": detail_success_count,
        "missing_tickers": missing_tickers,
        "list_date_present_count": list_date_present_count,
        "list_date_coverage": round(coverage, 6),
        "listing_date_coverage_passed": passed,
        "blockers": blockers,
        "derived_listing_date_sample": derived,
        "provider_query_performed": True,
        "provider_call_count": len(payloads),
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "ten_ticker_listing_date_coverage_only_not_pit_universe",
    }


def validate_polygon_listing_date_coverage_probe_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "derived_listing_date_coverage_sample.csv", "listing_date_coverage_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "listing_date_coverage_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "derived_listing_date_coverage_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "call_bound_respected", int(decision.get("provider_call_count", 0)) <= 10, str(decision.get("provider_call_count")))
    _check(checks, "scope_only", assessment.get("quality_scope") == "ten_ticker_listing_date_coverage_only_not_pit_universe", str(assessment.get("quality_scope")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _load_probe_tickers(manifest: dict[str, Any]) -> list[str]:
    sample_source = Path(str(manifest["sample_source"]))
    count = int(manifest["sample_ticker_count"])
    with sample_source.open("r", encoding="utf-8", newline="") as handle:
        return [str(row["ticker"]) for row in csv.DictReader(handle) if row.get("ticker")][:count]


def _load_polygon_api_key(env_path: str | Path = ".env") -> str:
    value = os.environ.get("POLYGON_API_KEY", "").strip()
    if value:
        return value
    path = Path(env_path)
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("POLYGON_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _fetch_polygon_ticker_details(api_key: str, ticker: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"apiKey": api_key})
    request = urllib.request.Request(f"https://api.polygon.io/v3/reference/tickers/{urllib.parse.quote(ticker)}?{query}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("listing_date_coverage_passed"))
    return {
        "status": "complete",
        "decision": "POLYGON_LISTING_DATE_COVERAGE_SUPPORT_PASS" if passed else "POLYGON_LISTING_DATE_COVERAGE_SUPPORT_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "expected_ticker_count": assessment.get("expected_ticker_count", 0),
        "detail_success_count": assessment.get("detail_success_count", 0),
        "list_date_present_count": assessment.get("list_date_present_count", 0),
        "list_date_coverage": assessment.get("list_date_coverage", 0.0),
        "blockers": assessment.get("blockers", []),
        "provider_query_performed": True,
        "provider_call_count": assessment.get("provider_call_count", 0),
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "next_unblocked_step": "If pass, preregister a PIT membership construction method before any broad-universe backtest.",
    }


def _blocked_decision(reason: str, *, provider_query: bool, call_count: int) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": provider_query,
        "provider_call_count": call_count,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
    }


def _empty_assessment(tickers: list[str], blockers: list[str], *, provider_query: bool) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "expected_tickers": tickers,
        "expected_ticker_count": len(tickers),
        "detail_success_count": 0,
        "missing_tickers": tickers,
        "list_date_present_count": 0,
        "list_date_coverage": 0.0,
        "listing_date_coverage_passed": False,
        "blockers": blockers,
        "derived_listing_date_sample": [],
        "provider_query_performed": provider_query,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "ten_ticker_listing_date_coverage_only_not_pit_universe",
    }


def _derived_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticker": str(row.get("ticker", "") or ""),
        "primary_exchange": str(row.get("primary_exchange", "") or ""),
        "type": str(row.get("type", "") or ""),
        "active": str(row.get("active", "")),
        "list_date": str(row.get("list_date", "") or ""),
        "cik": str(row.get("cik", "") or ""),
        "raw_payload_retained": False,
    }


def _write_vault_report(path: Path, assessment: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Listing Date Coverage Probe 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Bounded Polygon/Massive ticker details reference calls for ten active seed tickers. Only derived listing-date metadata retained. No market-data download, backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Expected tickers: {assessment['expected_ticker_count']}\n"
        f"- Provider calls: {decision.get('provider_call_count', 0)}\n"
        f"- Detail successes: {assessment['detail_success_count']}\n"
        f"- List-date present count: {assessment['list_date_present_count']}\n"
        f"- List-date coverage: {assessment['list_date_coverage']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This probe only tests bounded listing-date coverage. It does not authorize PIT universe construction or broad-universe backtests.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
    parser = argparse.ArgumentParser(description="Run Polygon listing-date coverage probe 001.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_polygon_listing_date_coverage_probe_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_polygon_listing_date_coverage_probe_001(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
