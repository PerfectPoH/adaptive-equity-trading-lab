from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_ticker_details_listing_date_probe_validator import (
    validate_polygon_ticker_details_listing_date_probe_gate,
)


RUN_ID = "POLYGON-TICKER-DETAILS-LISTING-DATE-PROBE-001"
TRIAL_ID = "UNIVERSE-LISTING-DATE-SOURCE-PROBE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_ticker_details_listing_date_probe_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-TICKER-DETAILS-LISTING-DATE-PROBE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Ticker-Details-Listing-Date-Probe-001-2026-05-24.md")


def run_polygon_ticker_details_listing_date_probe_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_ticker_details_listing_date_probe_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED", provider_query=False)
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    api_key = _load_polygon_api_key()
    if not api_key:
        assessment = _empty_assessment(["missing_polygon_api_key"])
        decision = _blocked_decision("BLOCKED_POLYGON_API_KEY_MISSING", provider_query=False)
    else:
        try:
            payload = _fetch_polygon_ticker_details(api_key, ticker=str(manifest["ticker"]))
            assessment = assess_ticker_details_listing_date_payload(payload)
            decision = _decision(assessment)
        except Exception as exc:  # pragma: no cover - network/entitlement path
            assessment = _empty_assessment(["provider_query_error"])
            assessment["provider_error"] = f"{type(exc).__name__}: {exc}"
            decision = _blocked_decision("BLOCKED_PROVIDER_ENTITLEMENT_OR_PAYLOAD", provider_query=True)
            decision["provider_error"] = assessment["provider_error"]
    rows = list(assessment.get("derived_listing_date_sample", []))
    _write_csv(output / "derived_listing_date_sample.csv", _fieldnames(rows), rows)
    _write_json(output / "listing_date_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_ticker_details_listing_date_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("results", {}) if isinstance(payload, dict) else {}
    list_date = str(result.get("list_date", "") or "").strip()
    ticker = str(result.get("ticker", "") or "").strip()
    blockers: list[str] = []
    if not ticker:
        blockers.append("missing_ticker")
    if not list_date:
        blockers.append("missing_list_date")
    passed = not blockers
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "ticker": ticker,
        "primary_exchange": str(result.get("primary_exchange", "") or ""),
        "type": str(result.get("type", "") or ""),
        "active": result.get("active"),
        "list_date": list_date,
        "cik": str(result.get("cik", "") or ""),
        "has_listing_date": bool(list_date),
        "listing_date_support_passed": passed,
        "blockers": blockers,
        "derived_listing_date_sample": [_derived_row(result)] if result else [],
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "single_ticker_listing_date_support_only_not_pit_universe",
    }


def validate_polygon_ticker_details_listing_date_probe_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "derived_listing_date_sample.csv", "listing_date_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "listing_date_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "derived_listing_date_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "scope_only", assessment.get("quality_scope") == "single_ticker_listing_date_support_only_not_pit_universe", str(assessment.get("quality_scope")))
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


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("listing_date_support_passed"))
    return {
        "status": "complete",
        "decision": "POLYGON_TICKER_DETAILS_LISTING_DATE_SUPPORT_PASS" if passed else "POLYGON_TICKER_DETAILS_LISTING_DATE_SUPPORT_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "ticker": assessment.get("ticker", ""),
        "list_date": assessment.get("list_date", ""),
        "blockers": assessment.get("blockers", []),
        "provider_query_performed": True,
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
        "next_unblocked_step": "If pass, preregister a multi-ticker listing-date coverage probe before PIT membership construction.",
    }


def _blocked_decision(reason: str, *, provider_query: bool) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": provider_query,
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


def _empty_assessment(blockers: list[str]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "ticker": "",
        "primary_exchange": "",
        "type": "",
        "active": None,
        "list_date": "",
        "cik": "",
        "has_listing_date": False,
        "listing_date_support_passed": False,
        "blockers": blockers,
        "derived_listing_date_sample": [],
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "quality_scope": "single_ticker_listing_date_support_only_not_pit_universe",
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
        "# Report Polygon Ticker Details Listing Date Probe 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single Polygon/Massive ticker details reference call for one active seed ticker. Only derived listing-date metadata retained. No market-data download, backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Ticker: {assessment['ticker']}\n"
        f"- List date: {assessment['list_date']}\n"
        f"- Has listing date: {assessment['has_listing_date']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This probe only tests single-ticker listing-date support. It does not authorize PIT universe construction or broad-universe backtests.\n"
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
        "gate_decision": "POLYGON_TICKER_DETAILS_LISTING_DATE_PROBE_OUTPUT_PASS" if failed == 0 else "POLYGON_TICKER_DETAILS_LISTING_DATE_PROBE_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon ticker details listing-date probe.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_polygon_ticker_details_listing_date_probe_001()
    report = validate_polygon_ticker_details_listing_date_probe_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
