from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_universe_quality_probe_validator import validate_polygon_universe_quality_probe_gate


RUN_ID = "POLYGON-UNIVERSE-QUALITY-PROBE-001"
TRIAL_ID = "UNIVERSE-QUALITY-PROBE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_universe_quality_probe_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-UNIVERSE-QUALITY-PROBE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Universe-Quality-Probe-001-2026-05-24.md")


def run_polygon_universe_quality_probe_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_universe_quality_probe_gate(spec_dir)
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
            payload = _fetch_polygon_active_tickers(api_key, limit=int(manifest["limit"]))
            assessment = assess_polygon_universe_quality_payload(payload, manifest=manifest)
            decision = _decision(assessment)
        except Exception as exc:  # pragma: no cover - network/entitlement path
            assessment = _empty_assessment(["provider_query_error"])
            assessment["provider_error"] = f"{type(exc).__name__}: {exc}"
            decision = _blocked_decision("BLOCKED_PROVIDER_ENTITLEMENT_OR_PAYLOAD", provider_query=True)
            decision["provider_error"] = assessment["provider_error"]

    sample = list(assessment.get("candidate_reference_sample", []))
    _write_csv(output / "candidate_reference_universe_sample.csv", _fieldnames(sample), sample)
    _write_json(output / "universe_quality_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_polygon_universe_quality_payload(payload: dict[str, Any], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = manifest or {
        "required_fields": ["ticker", "primary_exchange", "type", "active", "delisted_utc"],
        "required_exchanges": ["XNAS", "XNYS", "XASE"],
        "required_security_type": "CS",
        "min_candidate_common_stock_count": 300,
        "min_metadata_coverage": 0.95,
    }
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    required_fields = [str(field) for field in spec["required_fields"]]
    coverage = _metadata_coverage(rows, required_fields)
    required_exchanges = {str(exchange) for exchange in spec["required_exchanges"]}
    security_type = str(spec["required_security_type"])
    candidates = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("active") is True
        and str(row.get("type", "")) == security_type
        and str(row.get("primary_exchange", "")) in required_exchanges
        and bool(str(row.get("ticker", "")).strip())
    ]
    sample = _derived_rows(candidates[:100])
    blockers: list[str] = []
    if len(rows) < 300:
        blockers.append("record_count_below_300")
    if len(candidates) < int(spec["min_candidate_common_stock_count"]):
        blockers.append("candidate_count_below_300")
    low_coverage = [field for field, value in coverage.items() if value < float(spec["min_metadata_coverage"])]
    if low_coverage:
        blockers.append("metadata_coverage_below_0_95:" + ",".join(low_coverage))
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "record_count": len(rows),
        "candidate_common_stock_count": len(candidates),
        "required_exchanges": sorted(required_exchanges),
        "required_security_type": security_type,
        "metadata_coverage": coverage,
        "passes_reference_universe_quality": len(blockers) == 0,
        "blockers": blockers,
        "candidate_reference_sample": sample,
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "quality_scope": "reference_metadata_only_no_price_or_liquidity_claim",
    }


def validate_polygon_universe_quality_probe_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "candidate_reference_universe_sample.csv", "universe_quality_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "universe_quality_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "candidate_reference_universe_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "reference_scope_only", assessment.get("quality_scope") == "reference_metadata_only_no_price_or_liquidity_claim", str(assessment.get("quality_scope")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _metadata_coverage(rows: list[Any], required_fields: list[str]) -> dict[str, float]:
    if not rows:
        return {field: 0.0 for field in required_fields}
    total = len(rows)
    coverage: dict[str, float] = {}
    for field in required_fields:
        present = 0
        for row in rows:
            if isinstance(row, dict) and field in row:
                present += 1
        coverage[field] = present / total
    return coverage


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


def _fetch_polygon_active_tickers(api_key: str, *, limit: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {
            "market": "stocks",
            "locale": "us",
            "active": "true",
            "limit": str(limit),
            "apiKey": api_key,
        }
    )
    request = urllib.request.Request(f"https://api.polygon.io/v3/reference/tickers?{query}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _derived_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": str(row.get("ticker", "")),
            "market": str(row.get("market", "")),
            "locale": str(row.get("locale", "")),
            "primary_exchange": str(row.get("primary_exchange", "")),
            "type": str(row.get("type", "")),
            "active": str(row.get("active", "")),
            "delisted_utc": "" if row.get("delisted_utc") is None else str(row.get("delisted_utc", "")),
            "cik": str(row.get("cik", "")),
            "raw_payload_retained": False,
        }
        for row in rows
    ]


def _empty_assessment(blockers: list[str]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "record_count": 0,
        "candidate_common_stock_count": 0,
        "required_exchanges": ["XASE", "XNAS", "XNYS"],
        "required_security_type": "CS",
        "metadata_coverage": {},
        "passes_reference_universe_quality": False,
        "blockers": blockers,
        "candidate_reference_sample": [],
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "quality_scope": "reference_metadata_only_no_price_or_liquidity_claim",
    }


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("passes_reference_universe_quality"))
    return {
        "status": "complete",
        "decision": "POLYGON_UNIVERSE_REFERENCE_QUALITY_PASS" if passed else "POLYGON_UNIVERSE_REFERENCE_QUALITY_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "record_count": assessment.get("record_count", 0),
        "candidate_common_stock_count": assessment.get("candidate_common_stock_count", 0),
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
        "next_unblocked_step": "If pass, preregister a bounded liquidity/price availability probe before any universe backtest.",
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
    }


def _write_vault_report(path: Path, assessment: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Universe Quality Probe 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single bounded Polygon/Massive active ticker reference call. Only derived candidate rows and aggregate quality metrics retained. No market-data download, backtest, parameter sweep, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Records observed: {assessment['record_count']}\n"
        f"- Candidate active common stocks on XNAS/XNYS/XASE: {assessment['candidate_common_stock_count']}\n"
        f"- Metadata coverage: {json.dumps(assessment['metadata_coverage'], sort_keys=True)}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This probe only decides whether Polygon/Massive reference metadata can seed a future bounded liquidity probe. It does not create a final investable universe and does not authorize strategy tests.\n"
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
        "gate_decision": "POLYGON_UNIVERSE_QUALITY_PROBE_OUTPUT_PASS" if failed == 0 else "POLYGON_UNIVERSE_QUALITY_PROBE_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon universe quality reference probe.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_polygon_universe_quality_probe_001()
    report = validate_polygon_universe_quality_probe_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
