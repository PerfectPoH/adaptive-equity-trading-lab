from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.sec_company_tickers_universe_probe_validator import validate_sec_company_tickers_universe_probe_gate


RUN_ID = "SEC-COMPANY-TICKERS-UNIVERSE-PROBE-001"
TRIAL_ID = "UNIVERSE-SOURCE-PROBE-001"
SPEC_DIR = Path("experiments/provider_aware_research/sec_company_tickers_universe_probe_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/SEC-COMPANY-TICKERS-UNIVERSE-PROBE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC-Company-Tickers-Universe-Probe-001-2026-05-24.md")
SEC_UA = "adaptive-equity-trading-lab research-contact@example.com"


def run_sec_company_tickers_universe_probe_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_sec_company_tickers_universe_probe_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    try:
        payload = _fetch_sec_company_tickers()
        provider_error = None
    except Exception as exc:  # pragma: no cover - network failure path
        payload = {}
        provider_error = f"{type(exc).__name__}: {exc}"
    assessment = assess_sec_company_tickers_payload(payload)
    if provider_error:
        assessment["blockers"].append("provider_query_error")
        assessment["provider_error"] = provider_error
    sample = _derived_sample(payload, limit=25)
    decision = _decision(assessment)
    _write_csv(output / "derived_universe_sample.csv", _fieldnames(sample), sample)
    _write_json(output / "metadata_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_sec_company_tickers_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload.values()) if isinstance(payload, dict) else []
    keys = set().union(*(set(row.keys()) for row in rows if isinstance(row, dict))) if rows else set()
    has_ticker = "ticker" in keys
    has_cik = "cik_str" in keys
    has_exchange = "exchange" in keys or "primaryExchange" in keys
    has_security_type = "security_type" in keys or "securityType" in keys
    has_active_windows = {"first_trade_date", "last_trade_date"}.issubset(keys) or {"firstTradeDate", "lastTradeDate"}.issubset(keys)
    has_delisted_symbols = "delisted" in keys or "is_delisted" in keys or "delisted_symbols" in keys
    blockers: list[str] = []
    if not has_ticker:
        blockers.append("missing_ticker")
    if not has_cik:
        blockers.append("missing_cik")
    if not has_exchange:
        blockers.append("missing_exchange_metadata")
    if not has_security_type:
        blockers.append("missing_security_type_metadata")
    if not has_active_windows:
        blockers.append("missing_point_in_time_membership")
    if not has_delisted_symbols:
        blockers.append("missing_delisted_symbols")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "SEC",
        "endpoint": "https://www.sec.gov/files/company_tickers.json",
        "record_count": len(rows),
        "observed_fields": sorted(keys),
        "has_ticker": has_ticker,
        "has_cik": has_cik,
        "has_exchange": has_exchange,
        "has_security_type": has_security_type,
        "has_active_windows": has_active_windows,
        "has_delisted_symbols": has_delisted_symbols,
        "passes_universe_gate_requirements": len(blockers) == 0,
        "blockers": blockers,
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def validate_sec_company_tickers_universe_probe_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "derived_universe_sample.csv", "metadata_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    assessment = json.loads((path / "metadata_assessment.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "derived_universe_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"raw_payload", "raw_json"}
    _check(checks, "provider_query_recorded", decision.get("provider_query_performed") is True, str(decision.get("provider_query_performed")))
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _fetch_sec_company_tickers() -> dict[str, Any]:
    request = urllib.request.Request(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": SEC_UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _derived_sample(payload: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(payload.values())[:limit]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "cik": str(row.get("cik_str", "")).zfill(10) if row.get("cik_str") not in (None, "") else "",
                "symbol": str(row.get("ticker", "")),
                "title": str(row.get("title", "")),
                "exchange": str(row.get("exchange", "")),
                "security_type": str(row.get("security_type", "")),
                "first_trade_date": str(row.get("first_trade_date", "")),
                "last_trade_date": str(row.get("last_trade_date", "")),
                "raw_payload_retained": False,
            }
        )
    return rows


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("passes_universe_gate_requirements"))
    return {
        "status": "complete",
        "decision": "SEC_COMPANY_TICKERS_UNIVERSE_SOURCE_PASS" if passed else "SEC_COMPANY_TICKERS_UNIVERSE_SOURCE_BLOCKED_METADATA_INSUFFICIENT",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "record_count": assessment.get("record_count", 0),
        "candidate_source_allowed": passed,
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
        "next_unblocked_step": "If blocked, select another universe provider with PIT membership, security type, exchange and delisted-symbol metadata.",
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, assessment: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report SEC Company Tickers Universe Probe 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single official SEC company_tickers.json call. Only derived sample and metadata assessment retained. No market-data download, backtest, parameter sweep, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Records observed: {assessment['record_count']}\n"
        f"- Observed fields: {', '.join(assessment['observed_fields'])}\n"
        f"- Has ticker: {assessment['has_ticker']}\n"
        f"- Has CIK: {assessment['has_cik']}\n"
        f"- Has exchange metadata: {assessment['has_exchange']}\n"
        f"- Has security type metadata: {assessment['has_security_type']}\n"
        f"- Has active windows: {assessment['has_active_windows']}\n"
        f"- Has delisted symbols: {assessment['has_delisted_symbols']}\n"
        f"- Blockers: {', '.join(decision['blockers'])}\n\n"
        "## Interpretation\n\n"
        "SEC company_tickers.json can support ticker-to-CIK joins, but it is not a sufficient universe source for rare-event alpha research if it lacks point-in-time membership, delisted symbols, exchange and security-type metadata.\n"
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
        "gate_decision": "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_OUTPUT_PASS" if failed == 0 else "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC company tickers universe source probe.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_sec_company_tickers_universe_probe_001()
    report = validate_sec_company_tickers_universe_probe_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
