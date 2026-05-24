from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_listing_date_coverage_continuation_validator import (
    validate_polygon_listing_date_coverage_continuation_gate,
)


RUN_ID = "POLYGON-LISTING-DATE-COVERAGE-CONTINUATION-001"
TRIAL_ID = "UNIVERSE-LISTING-DATE-COVERAGE-CONTINUATION-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_listing_date_coverage_continuation_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-LISTING-DATE-COVERAGE-CONTINUATION-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Listing-Date-Coverage-Continuation-001-2026-05-24.md")


def run_polygon_listing_date_coverage_continuation_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_listing_date_coverage_continuation_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED", provider_query=False, call_count=0)
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    tickers = list(manifest["remaining_tickers"])
    delay = int(manifest["min_seconds_between_calls"])
    api_key = _load_polygon_api_key()
    if not api_key:
        assessment = _empty_assessment(tickers, ["missing_polygon_api_key"], provider_query=False)
        decision = _blocked_decision("BLOCKED_POLYGON_API_KEY_MISSING", provider_query=False, call_count=0)
    else:
        payloads: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        attempted_count = 0
        for index, ticker in enumerate(tickers):
            if index > 0:
                _sleep_between_calls(delay)
            attempted_count += 1
            try:
                payloads.append(_fetch_polygon_ticker_details(api_key, ticker=ticker))
            except Exception as exc:  # pragma: no cover - network path
                errors.append({"ticker": ticker, "error": f"{type(exc).__name__}: {exc}"})
        assessment = assess_continuation_listing_date_coverage(payloads, expected_tickers=tickers)
        assessment["provider_errors"] = errors
        assessment["provider_call_count"] = attempted_count
        assessment["provider_error_count"] = len(errors)
        assessment["provider_success_count"] = len(payloads)
        decision = _decision(assessment)
    rows = list(assessment.get("derived_listing_date_sample", []))
    _write_csv(output / "derived_listing_date_continuation_sample.csv", _fieldnames(rows), rows)
    _write_json(output / "listing_date_continuation_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_continuation_listing_date_coverage(payloads: list[dict[str, Any]], *, expected_tickers: list[str]) -> dict[str, Any]:
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
    success_count = len(derived)
    list_date_present_count = sum(1 for row in derived if row["list_date"])
    missing_tickers = [ticker for ticker in expected_tickers if ticker not in seen]
    blockers: list[str] = []
    if success_count < len(expected_tickers):
        blockers.append("detail_success_count_below_5")
    if list_date_present_count < len(expected_tickers):
        blockers.append("list_date_present_count_below_5")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "expected_tickers": expected_tickers,
        "expected_ticker_count": len(expected_tickers),
        "detail_success_count": success_count,
        "provider_success_count": success_count,
        "provider_error_count": 0,
        "provider_call_count": len(payloads),
        "missing_tickers": missing_tickers,
        "list_date_present_count": list_date_present_count,
        "continuation_passed": not blockers,
        "blockers": blockers,
        "derived_listing_date_sample": derived,
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "five_ticker_rate_limited_listing_date_continuation_only_not_pit_universe",
    }


def validate_polygon_listing_date_coverage_continuation_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "derived_listing_date_continuation_sample.csv", "listing_date_continuation_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "listing_date_continuation_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "derived_listing_date_continuation_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "call_bound_respected", int(decision.get("provider_call_count", 0)) <= 5, str(decision.get("provider_call_count")))
    _check(checks, "scope_only", assessment.get("quality_scope") == "five_ticker_rate_limited_listing_date_continuation_only_not_pit_universe", str(assessment.get("quality_scope")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


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


def _sleep_between_calls(seconds: int) -> None:
    time.sleep(seconds)


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("continuation_passed"))
    return {
        "status": "complete",
        "decision": "POLYGON_LISTING_DATE_COVERAGE_CONTINUATION_PASS" if passed else "POLYGON_LISTING_DATE_COVERAGE_CONTINUATION_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "expected_ticker_count": assessment.get("expected_ticker_count", 0),
        "detail_success_count": assessment.get("detail_success_count", 0),
        "list_date_present_count": assessment.get("list_date_present_count", 0),
        "blockers": assessment.get("blockers", []),
        "provider_query_performed": True,
        "provider_call_count": assessment.get("provider_call_count", 0),
        "provider_success_count": assessment.get("provider_success_count", 0),
        "provider_error_count": assessment.get("provider_error_count", 0),
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
        "next_unblocked_step": "If pass, combine coverage probes in a no-query PIT construction policy gate before any broad-universe backtest.",
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
        "provider_success_count": 0,
        "provider_error_count": 0,
        "provider_call_count": 0,
        "missing_tickers": tickers,
        "list_date_present_count": 0,
        "continuation_passed": False,
        "blockers": blockers,
        "derived_listing_date_sample": [],
        "provider_query_performed": provider_query,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "five_ticker_rate_limited_listing_date_continuation_only_not_pit_universe",
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
        "# Report Polygon Listing Date Coverage Continuation 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Bounded continuation for the five ticker details calls that hit provider rate limits in the prior coverage probe. Only derived listing-date metadata retained. No market-data download, backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Expected tickers: {assessment['expected_ticker_count']}\n"
        f"- Provider calls: {decision.get('provider_call_count', 0)}\n"
        f"- Provider successes: {decision.get('provider_success_count', 0)}\n"
        f"- Provider errors: {decision.get('provider_error_count', 0)}\n"
        f"- List-date present count: {assessment['list_date_present_count']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This continuation only tests bounded listing-date coverage for rate-limited tickers. It does not authorize PIT universe construction or broad-universe backtests.\n"
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
    parser = argparse.ArgumentParser(description="Run Polygon listing-date coverage continuation 001.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_polygon_listing_date_coverage_continuation_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_polygon_listing_date_coverage_continuation_001(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
