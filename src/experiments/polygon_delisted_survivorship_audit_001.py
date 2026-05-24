from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_delisted_survivorship_audit_validator import validate_polygon_delisted_survivorship_audit_gate


RUN_ID = "POLYGON-DELISTED-SURVIVORSHIP-AUDIT-001"
TRIAL_ID = "UNIVERSE-SURVIVORSHIP-AUDIT-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_delisted_survivorship_audit_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-DELISTED-SURVIVORSHIP-AUDIT-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Delisted-Survivorship-Audit-001-2026-05-24.md")


def run_polygon_delisted_survivorship_audit_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_delisted_survivorship_audit_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED", provider_query=False)
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = json.loads((Path(spec_dir) / "audit_manifest.json").read_text(encoding="utf-8"))
    api_key = _load_polygon_api_key()
    if not api_key:
        assessment = _empty_assessment(["missing_polygon_api_key"])
        decision = _blocked_decision("BLOCKED_POLYGON_API_KEY_MISSING", provider_query=False)
    else:
        try:
            payload = _fetch_polygon_inactive_tickers(api_key, limit=int(manifest["limit"]))
            assessment = assess_polygon_delisted_payload(payload, manifest=manifest)
            decision = _decision(assessment)
        except Exception as exc:  # pragma: no cover - network/entitlement path
            assessment = _empty_assessment(["provider_query_error"])
            assessment["provider_error"] = f"{type(exc).__name__}: {exc}"
            decision = _blocked_decision("BLOCKED_PROVIDER_ENTITLEMENT_OR_PAYLOAD", provider_query=True)
            decision["provider_error"] = assessment["provider_error"]
    rows = list(assessment.get("delisted_reference_sample", []))
    _write_csv(output / "delisted_reference_sample.csv", _fieldnames(rows), rows)
    _write_json(output / "delisted_survivorship_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_polygon_delisted_payload(payload: dict[str, Any], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = manifest or {
        "required_security_type": "CS",
        "min_delisted_common_stock_count": 300,
        "min_delisted_date_coverage": 0.95,
    }
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    candidates = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("active") is False
        and str(row.get("type", "")) == str(spec["required_security_type"])
        and bool(str(row.get("ticker", "")).strip())
    ]
    with_dates = [row for row in candidates if bool(str(row.get("delisted_utc", "")).strip())]
    coverage = len(with_dates) / len(candidates) if candidates else 0.0
    blockers: list[str] = []
    if len(candidates) < int(spec["min_delisted_common_stock_count"]):
        blockers.append("delisted_common_stock_count_below_300")
    if coverage < float(spec["min_delisted_date_coverage"]):
        blockers.append("delisted_date_coverage_below_0_95")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "record_count": len(rows),
        "delisted_common_stock_count": len(candidates),
        "delisted_date_coverage": coverage,
        "passes_delisted_metadata_support": len(blockers) == 0,
        "blockers": blockers,
        "delisted_reference_sample": _derived_rows(candidates[:100]),
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "pit_universe_backtest_authorized": False,
        "requires_pit_membership_construction": True,
        "quality_scope": "delisted_metadata_support_only_not_full_pit_universe",
    }


def validate_polygon_delisted_survivorship_audit_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "delisted_reference_sample.csv", "delisted_survivorship_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "delisted_survivorship_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "delisted_reference_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "pit_backtest_not_authorized", decision.get("pit_universe_backtest_authorized") is False, str(decision.get("pit_universe_backtest_authorized")))
    _check(checks, "pit_construction_still_required", decision.get("requires_pit_membership_construction") is True, str(decision.get("requires_pit_membership_construction")))
    _check(checks, "scope_only", assessment.get("quality_scope") == "delisted_metadata_support_only_not_full_pit_universe", str(assessment.get("quality_scope")))
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


def _fetch_polygon_inactive_tickers(api_key: str, *, limit: int) -> dict[str, Any]:
    query = urllib.parse.urlencode({"market": "stocks", "locale": "us", "active": "false", "limit": str(limit), "apiKey": api_key})
    request = urllib.request.Request(f"https://api.polygon.io/v3/reference/tickers?{query}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("passes_delisted_metadata_support"))
    return {
        "status": "complete",
        "decision": "POLYGON_DELISTED_METADATA_SUPPORT_PASS" if passed else "POLYGON_DELISTED_METADATA_SUPPORT_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "record_count": assessment.get("record_count", 0),
        "delisted_common_stock_count": assessment.get("delisted_common_stock_count", 0),
        "delisted_date_coverage": assessment.get("delisted_date_coverage", 0.0),
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
        "pit_universe_backtest_authorized": False,
        "requires_pit_membership_construction": True,
        "next_unblocked_step": "Construct and preregister a PIT universe membership policy before any broad-universe strategy backtest.",
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
        "pit_universe_backtest_authorized": False,
        "requires_pit_membership_construction": True,
    }


def _empty_assessment(blockers: list[str]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "record_count": 0,
        "delisted_common_stock_count": 0,
        "delisted_date_coverage": 0.0,
        "passes_delisted_metadata_support": False,
        "blockers": blockers,
        "delisted_reference_sample": [],
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "pit_universe_backtest_authorized": False,
        "requires_pit_membership_construction": True,
        "quality_scope": "delisted_metadata_support_only_not_full_pit_universe",
    }


def _derived_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": str(row.get("ticker", "")),
            "primary_exchange": str(row.get("primary_exchange", "")),
            "type": str(row.get("type", "")),
            "active": str(row.get("active", "")),
            "delisted_utc": str(row.get("delisted_utc", "")),
            "cik": str(row.get("cik", "")),
            "raw_payload_retained": False,
        }
        for row in rows
    ]


def _write_vault_report(path: Path, assessment: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Delisted Survivorship Audit 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single bounded Polygon/Massive inactive ticker reference call. Only derived delisted reference rows and metadata support metrics retained. No market-data download, backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Records observed: {assessment['record_count']}\n"
        f"- Delisted common stocks: {assessment['delisted_common_stock_count']}\n"
        f"- Delisted date coverage: {assessment['delisted_date_coverage']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This audit proves delisted metadata support only. It still does not authorize broad-universe backtests because PIT membership construction remains a separate required step.\n"
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
        "gate_decision": "POLYGON_DELISTED_SURVIVORSHIP_AUDIT_OUTPUT_PASS" if failed == 0 else "POLYGON_DELISTED_SURVIVORSHIP_AUDIT_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon delisted survivorship audit.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_polygon_delisted_survivorship_audit_001()
    report = validate_polygon_delisted_survivorship_audit_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
