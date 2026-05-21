from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.experiments.xmom_earnings_single_probe_approval_validator import (
    validate_xmom_earnings_single_probe_approval,
)
from src.experiments.xmom_earnings_single_probe_execution_preflight_validator import (
    validate_xmom_earnings_single_probe_execution_preflight,
)
from src.validation.earnings_timestamp_classifier import classify_earnings_timestamp


DEFAULT_APPROVAL_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521"
DEFAULT_EXPLICIT_APPROVAL_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_20260521"
DEFAULT_OUTPUT_DIR = "experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001"
DEFAULT_LEDGER_PATH = "experiments/provider_aware_research/trial_ledger/xmom_earnings_single_probe_trial_ledger.csv"
EXPECTED_GATE_ID = "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001"
EXPECTED_TRIAL_ID = "TRIAL-XMOM-CATALYST-001"
INTRINIO_BASE_URL = "https://api-v2.intrinio.com"
REQUIRED_REAL_RUN_GATES = {
    "explicit_single_probe_approval_granted",
    "provider_selected",
    "symbol_selected",
    "endpoint_selected",
    "immutable_output_directory_created",
    "trial_ledger_entry_created",
    "raw_payload_retention_blocked",
}
FORBIDDEN_FLAGS = {
    "--all-symbols",
    "--multi-provider",
    "--download-market-data",
    "--save-raw-payload",
    "--implement-extractor",
    "--run-oos",
    "--paper",
    "--live",
    "--promote",
}


def build_dry_run_plan(
    *,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    provider: str = "unselected",
    symbol: str = "unselected",
    endpoint: str = "earnings_calendar_or_equivalent",
    output_dir: str = "not_created",
) -> dict[str, Any]:
    approval_report = validate_xmom_earnings_single_probe_approval(approval_dir)
    return {
        "status": "dry_run_only",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "approval_dir": str(approval_dir),
        "approval_gate_status": approval_report["status"],
        "approval_gate_decision": approval_report["gate_decision"],
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "planned_output_dir": output_dir,
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "required_next_approval": "explicit_single_probe_approval_granted",
        "blocked_actions": sorted(FORBIDDEN_FLAGS),
    }


def build_real_run_block_report(
    *,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    provider: str = "unselected",
    symbol: str = "unselected",
    endpoint: str = "earnings_calendar_or_equivalent",
    output_dir: str = "not_created",
    acknowledged_gates: set[str] | None = None,
) -> dict[str, Any]:
    approval_report = validate_xmom_earnings_single_probe_approval(approval_dir)
    manifest = _read_manifest(Path(approval_dir))
    acknowledged = acknowledged_gates or set()
    missing = set(REQUIRED_REAL_RUN_GATES - acknowledged)
    if manifest.get("approval_status") != "granted":
        missing.add("explicit_single_probe_approval_granted")
    if provider in {"", "unselected"}:
        missing.add("provider_selected")
    if symbol in {"", "unselected"}:
        missing.add("symbol_selected")
    if endpoint in {"", "unselected"}:
        missing.add("endpoint_selected")
    if output_dir in {"", "not_created"}:
        missing.add("immutable_output_directory_created")
    if manifest.get("raw_payload_retention_allowed") is not False:
        missing.add("raw_payload_retention_blocked")

    return {
        "status": "blocked",
        "error": "single_probe_real_run_gates_unresolved",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "approval_dir": str(approval_dir),
        "approval_gate_status": approval_report["status"],
        "approval_gate_decision": approval_report["gate_decision"],
        "approval_status": manifest.get("approval_status", "missing"),
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "planned_output_dir": output_dir,
        "required_gates": sorted(REQUIRED_REAL_RUN_GATES),
        "acknowledged_gates": sorted(acknowledged),
        "missing_gates": sorted(missing),
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


def run_intrinio_single_earnings_probe(
    *,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    explicit_approval_dir: str | Path = DEFAULT_EXPLICIT_APPROVAL_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    provider: str = "Intrinio",
    symbol: str = "CRMD",
    endpoint: str = "companies/{identifier}/upcoming_earnings",
    expected_date_after: str = "2024-01-01",
    expected_date_before: str = "2025-12-31",
    max_provider_calls: int = 1,
) -> dict[str, Any]:
    preflight = validate_xmom_earnings_single_probe_execution_preflight(
        approval_gate_dir=approval_dir,
        explicit_approval_dir=explicit_approval_dir,
        output_dir=output_dir,
        ledger_path=ledger_path,
    )
    if preflight["status"] != "pass":
        return _execution_blocked("preflight_not_passed", preflight)
    if provider.lower() != "intrinio":
        return _execution_blocked("unsupported_provider", {"provider": provider})
    if max_provider_calls != 1:
        return _execution_blocked("provider_call_budget_must_equal_one", {"max_provider_calls": max_provider_calls})

    api_key = _load_intrinio_api_key()
    if not api_key:
        return _execution_blocked("intrinio_api_key_missing", {"env_var": "INTRINIO_API_KEY"})

    output_path = Path(output_dir)
    execution_manifest_path = output_path / "single_probe_execution_manifest.json"
    if execution_manifest_path.exists():
        return _execution_blocked("execution_manifest_already_exists", {"path": str(execution_manifest_path)})

    query_url = _intrinio_upcoming_earnings_url(
        symbol=symbol,
        expected_date_after=expected_date_after,
        expected_date_before=expected_date_before,
        page_size=10,
        api_key=api_key,
    )
    try:
        payload = _fetch_json(query_url)
    except HTTPError as exc:
        result = _provider_error_result(
            provider=provider,
            symbol=symbol,
            endpoint=endpoint,
            code=f"HTTP_ERROR_{exc.code}",
            detail=str(exc.reason),
        )
        _write_json(execution_manifest_path, result)
        _update_trial_ledger(ledger_path, result)
        return result
    except URLError as exc:
        result = _provider_error_result(
            provider=provider,
            symbol=symbol,
            endpoint=endpoint,
            code="URL_ERROR",
            detail=str(exc.reason),
        )
        _write_json(execution_manifest_path, result)
        _update_trial_ledger(ledger_path, result)
        return result

    result = _summarize_intrinio_earnings_payload(
        payload,
        provider=provider,
        symbol=symbol,
        endpoint=endpoint,
        expected_date_after=expected_date_after,
        expected_date_before=expected_date_before,
    )
    _write_json(execution_manifest_path, result)
    _update_trial_ledger(ledger_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args, unknown = parser.parse_known_args(argv)
    forbidden = sorted(FORBIDDEN_FLAGS.intersection(unknown))
    if forbidden:
        print(json.dumps(_blocked("forbidden_flags_present", f"forbidden={forbidden}"), indent=2, sort_keys=True))
        return 2
    if args.execute:
        print(json.dumps(_blocked("execute_forbidden", "--execute is not supported by this gated runner."), indent=2, sort_keys=True))
        return 2
    if not args.dry_run and not args.real_run:
        print(json.dumps(_blocked("mode_required", "Pass --dry-run or --real-run."), indent=2, sort_keys=True))
        return 2
    if args.dry_run and args.real_run:
        print(json.dumps(_blocked("conflicting_modes", "Choose only one mode."), indent=2, sort_keys=True))
        return 2
    if args.real_run:
        missing_ack = REQUIRED_REAL_RUN_GATES - set(args.acknowledge_gate)
        if missing_ack:
            report = build_real_run_block_report(
                approval_dir=args.approval_dir,
                provider=args.provider,
                symbol=args.symbol,
                endpoint=args.endpoint,
                output_dir=args.output_dir,
                acknowledged_gates=set(args.acknowledge_gate),
            )
            print(json.dumps(report, indent=2, sort_keys=True))
            return 2
        report = run_intrinio_single_earnings_probe(
            approval_dir=args.approval_dir,
            explicit_approval_dir=args.explicit_approval_dir,
            output_dir=args.output_dir,
            ledger_path=args.ledger_path,
            provider=args.provider,
            symbol=args.symbol,
            endpoint=args.endpoint,
            expected_date_after=args.expected_date_after,
            expected_date_before=args.expected_date_before,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] in {"pass", "provider_error_recorded"} else 2

    report = build_dry_run_plan(
        approval_dir=args.approval_dir,
        provider=args.provider,
        symbol=args.symbol,
        endpoint=args.endpoint,
        output_dir=args.output_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gated dry-run runner for XMOM earnings single metadata probe.")
    parser.add_argument("--dry-run", action="store_true", help="Build a non-executing plan.")
    parser.add_argument("--real-run", action="store_true", help="Return a blocked real-run gate report.")
    parser.add_argument("--execute", action="store_true", help="Forbidden. Present only to fail safely if attempted.")
    parser.add_argument("--approval-dir", default=DEFAULT_APPROVAL_DIR)
    parser.add_argument("--explicit-approval-dir", default=DEFAULT_EXPLICIT_APPROVAL_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--provider", default="Intrinio")
    parser.add_argument("--symbol", default="CRMD")
    parser.add_argument("--endpoint", default="companies/{identifier}/upcoming_earnings")
    parser.add_argument("--expected-date-after", default="2024-01-01")
    parser.add_argument("--expected-date-before", default="2025-12-31")
    parser.add_argument("--acknowledge-gate", action="append", default=[], choices=sorted(REQUIRED_REAL_RUN_GATES))
    return parser


def _read_manifest(approval_dir: Path) -> dict[str, Any]:
    path = approval_dir / "single_probe_approval_manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _blocked(error: str, detail: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": error,
        "detail": detail,
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


def _execution_blocked(error: str, detail: Any) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": error,
        "detail": detail,
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


def _load_intrinio_api_key() -> str:
    api_key = os.environ.get("INTRINIO_API_KEY", "").strip()
    if api_key:
        return api_key
    env_path = Path(".env")
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("INTRINIO_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _intrinio_upcoming_earnings_url(
    *,
    symbol: str,
    expected_date_after: str,
    expected_date_before: str,
    page_size: int,
    api_key: str,
) -> str:
    query = urlencode(
        {
            "expected_date_after": expected_date_after,
            "expected_date_before": expected_date_before,
            "page_size": page_size,
            "api_key": api_key,
        }
    )
    return f"{INTRINIO_BASE_URL}/companies/{symbol}/upcoming_earnings?{query}"


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-xmom-earnings-probe"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _summarize_intrinio_earnings_payload(
    payload: dict[str, Any],
    *,
    provider: str,
    symbol: str,
    endpoint: str,
    expected_date_after: str,
    expected_date_before: str,
) -> dict[str, Any]:
    records = _extract_earnings_records(payload)
    first = records[0] if records else {}
    timestamp_candidates = _classify_timestamp_candidates(first)
    return {
        "status": "pass",
        "decision": "XMOM_EARNINGS_SINGLE_PROBE_EXECUTED_REDACTED_SUMMARY_ONLY",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "expected_date_after": expected_date_after,
        "expected_date_before": expected_date_before,
        "provider_query_performed": True,
        "network_call_performed": True,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "payload_top_level_keys": sorted(payload.keys()),
        "record_count": len(records),
        "first_record_keys": sorted(first.keys()),
        "timestamp_candidates": timestamp_candidates,
        "timestamp_resolution_verdict": _timestamp_resolution_verdict(timestamp_candidates),
        "api_key": "REDACTED",
    }


def _extract_earnings_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("expected_earnings", "upcoming_earnings", "earnings", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _classify_timestamp_candidates(record: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    for key, value in sorted(record.items()):
        lowered = key.lower()
        if "date" not in lowered and "time" not in lowered and "at" not in lowered:
            continue
        if not isinstance(value, str):
            candidates[key] = {"type": type(value).__name__, "classification": "NON_STRING_SKIPPED"}
            continue
        classification = classify_earnings_timestamp(value)
        candidates[key] = {
            "type": "str",
            "classification": classification.classification,
            "action": classification.action,
            "reason": classification.reason,
            "local_timestamp_present": classification.local_timestamp is not None,
            "reaction_session": classification.reaction_session,
        }
    return candidates


def _timestamp_resolution_verdict(timestamp_candidates: dict[str, Any]) -> str:
    if not timestamp_candidates:
        return "NO_TIMESTAMP_FIELDS_DETECTED"
    classifications = {value.get("classification") for value in timestamp_candidates.values() if isinstance(value, dict)}
    if classifications.intersection({"BMO", "AMC", "DMT"}):
        return "INTRADAY_TIMESTAMP_CLASSIFIABLE"
    return "DATE_ONLY_OR_UNSPECIFIED"


def _provider_error_result(*, provider: str, symbol: str, endpoint: str, code: str, detail: str) -> dict[str, Any]:
    return {
        "status": "provider_error_recorded",
        "decision": "XMOM_EARNINGS_SINGLE_PROBE_PROVIDER_ERROR_REDACTED",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "error": code,
        "detail": detail,
        "provider_query_performed": True,
        "network_call_performed": True,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "api_key": "REDACTED",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _update_trial_ledger(ledger_path: str | Path, result: dict[str, Any]) -> None:
    path = Path(ledger_path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        base_fields = list(reader.fieldnames or [])
    if not rows:
        return
    extra_fields = [
        "provider_query_performed",
        "network_call_performed",
        "error",
        "timestamp_resolution_verdict",
    ]
    fieldnames = base_fields + [field for field in extra_fields if field not in base_fields]
    rows[0]["result_status"] = result.get("status", "unknown")
    rows[0]["decision"] = result.get("decision", "unknown")
    rows[0]["provider_query_performed"] = str(result.get("provider_query_performed", False)).lower()
    rows[0]["network_call_performed"] = str(result.get("network_call_performed", False)).lower()
    rows[0]["error"] = str(result.get("error", ""))
    rows[0]["timestamp_resolution_verdict"] = str(result.get("timestamp_resolution_verdict", ""))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
