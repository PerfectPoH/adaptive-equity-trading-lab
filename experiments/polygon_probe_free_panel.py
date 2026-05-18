from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import dotenv_values


DEFAULT_EVALUATION_DIR = Path("experiments/provider_evaluations/polygon_stocks_basic_free_20260518")
API_KEY_ENV_NAME = "POLYGON_API_KEY"
POLYGON_BASE_URL = "https://api.polygon.io"


@dataclass(frozen=True)
class PolygonCheck:
    event_id: str
    symbol: str
    capability: str
    path: str
    params: dict[str, str]


PANEL_CHECKS = [
    PolygonCheck("DPE-002", "MULN", "reverse_split_reference", "/v3/reference/splits", {"ticker": "MULN", "execution_date.gte": "2023-12-01", "execution_date.lte": "2024-01-15", "limit": "10"}),
    PolygonCheck("DPE-005", "WEYS", "dividend_reference", "/v3/reference/dividends", {"ticker": "WEYS", "ex_dividend_date.gte": "2024-10-01", "ex_dividend_date.lte": "2024-12-15", "limit": "10"}),
    PolygonCheck("DPE-010", "DJT", "ticker_details_reference", "/v3/reference/tickers/DJT", {"date": "2024-03-26"}),
    PolygonCheck("DPE-010", "DJT", "minute_aggregate", "/v2/aggs/ticker/DJT/range/1/minute/2024-03-26/2024-03-26", {"adjusted": "true", "sort": "asc", "limit": "5"}),
    PolygonCheck("DPE-006", "FSR", "delisted_ticker_details", "/v3/reference/tickers/FSR", {"date": "2024-03-20"}),
]


@dataclass(frozen=True)
class PolygonProbeConfig:
    evaluation_dir: Path
    env_file: Path
    api_key_source: str
    dry_run: bool
    retain_raw_response: bool
    sleep_seconds: float
    max_checks: int


class ApiKeySourceError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = PolygonProbeConfig(
        evaluation_dir=Path(args.evaluation_dir),
        env_file=Path(args.env_file),
        api_key_source=args.api_key_source,
        dry_run=args.dry_run,
        retain_raw_response=args.retain_raw_response,
        sleep_seconds=args.sleep_seconds,
        max_checks=args.max_checks,
    )
    try:
        api_key, key_diagnostics = _resolve_api_key(config.api_key_source, config.env_file)
    except ApiKeySourceError as exc:
        print(f"POLYGON_KEY_ERROR:{exc.code}", file=sys.stderr)
        return 2
    if not api_key:
        print("POLYGON_API_KEY_MISSING", file=sys.stderr)
        return 2
    checks = PANEL_CHECKS[: config.max_checks]
    if config.dry_run:
        print(json.dumps({"status": "dry_run", "api_key": "REDACTED", **key_diagnostics, "checks": [_redacted_check_url(c) for c in checks]}, indent=2, sort_keys=True))
        return 0
    if not config.evaluation_dir.exists():
        print(f"EVALUATION_DIR_MISSING: {config.evaluation_dir}", file=sys.stderr)
        return 3
    results = []
    for index, check in enumerate(checks):
        if index > 0:
            time.sleep(config.sleep_seconds)
        try:
            payload = _fetch_json(check, api_key)
            result = _summarize_payload(check, payload, status="pass")
            if config.retain_raw_response:
                result["raw_response_path"] = str(_write_raw_response(config, check, payload)).replace("\\", "/")
        except HTTPError as exc:
            result = _summarize_error(check, f"HTTP_ERROR_{exc.code}", exc.reason)
        except URLError as exc:
            result = _summarize_error(check, "URL_ERROR", str(exc.reason))
        results.append(result)
    _write_probe_summary(config, results)
    _update_artifacts(config, results)
    print(json.dumps({"status": "completed", "api_key": "REDACTED", **key_diagnostics, "checks_executed": len(results), "results": results}, indent=2, sort_keys=True))
    return 0 if any(r["status"] == "pass" for r in results) else 5


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run controlled Polygon Stocks Basic Free provider-evaluation probes.")
    parser.add_argument("--evaluation-dir", default=str(DEFAULT_EVALUATION_DIR))
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--api-key-source", choices=["auto", "environment", "env-file"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retain-raw-response", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=13.0)
    parser.add_argument("--max-checks", type=int, default=len(PANEL_CHECKS))
    return parser


def _resolve_api_key(api_key_source: str, env_file: Path) -> tuple[str, dict[str, str | bool]]:
    env_key = os.environ.get(API_KEY_ENV_NAME, "")
    file_key = ""
    if env_file.exists():
        file_key = str(dotenv_values(env_file).get(API_KEY_ENV_NAME) or "")
    if api_key_source == "environment":
        return env_key, _api_key_diagnostics(api_key_source, "environment", env_file, env_key, file_key, env_key)
    if api_key_source == "env-file":
        return file_key, _api_key_diagnostics(api_key_source, "env-file", env_file, env_key, file_key, file_key)
    if env_key and file_key and env_key != file_key:
        raise ApiKeySourceError("POLYGON_API_KEY_SOURCE_CONFLICT", "Process environment and env file contain different Polygon keys.")
    if env_key:
        return env_key, _api_key_diagnostics(api_key_source, "environment", env_file, env_key, file_key, env_key)
    if file_key:
        return file_key, _api_key_diagnostics(api_key_source, "env-file", env_file, env_key, file_key, file_key)
    return "", _api_key_diagnostics(api_key_source, "missing", env_file, env_key, file_key, "")


def _api_key_diagnostics(requested: str, resolved: str, env_file: Path, env_key: str, file_key: str, selected_key: str) -> dict[str, str | bool]:
    return {
        "api_key_source_requested": requested,
        "api_key_source_resolved": resolved,
        "api_key_fingerprint": _fingerprint_secret(selected_key),
        "environment_key_present": bool(env_key),
        "environment_key_fingerprint": _fingerprint_secret(env_key),
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "env_file_key_present": bool(file_key),
        "env_file_key_fingerprint": _fingerprint_secret(file_key),
    }


def _fetch_json(check: PolygonCheck, api_key: str) -> dict:
    params = {**check.params, "apiKey": api_key}
    url = f"{POLYGON_BASE_URL}{check.path}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-provider-eval"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _redacted_check_url(check: PolygonCheck) -> dict[str, object]:
    return {"event_id": check.event_id, "symbol": check.symbol, "capability": check.capability, "path": check.path, "params": check.params}


def _summarize_payload(check: PolygonCheck, payload: dict, status: str) -> dict[str, object]:
    results = payload.get("results")
    if isinstance(results, list):
        result_count = len(results)
        fields = sorted({key for row in results[:5] if isinstance(row, dict) for key in row.keys()})
    elif isinstance(results, dict):
        result_count = 1
        fields = sorted(results.keys())
    else:
        result_count = 0
        fields = sorted(payload.keys())
    return {
        "event_id": check.event_id,
        "symbol": check.symbol,
        "capability": check.capability,
        "status": status,
        "http_status": payload.get("status", "unknown"),
        "result_count": result_count,
        "fields_preview": "|".join(fields[:25]),
        "payload_sha256": _sha256_json(payload),
        "raw_response_path": "RAW_RESPONSE_RETENTION_NOT_ENABLED",
    }


def _summarize_error(check: PolygonCheck, code: str, detail: str) -> dict[str, object]:
    return {
        "event_id": check.event_id,
        "symbol": check.symbol,
        "capability": check.capability,
        "status": "error",
        "http_status": code,
        "result_count": 0,
        "fields_preview": "",
        "payload_sha256": _sha256_json({"code": code, "detail": detail}),
        "raw_response_path": "RAW_RESPONSE_RETENTION_NOT_ENABLED",
    }


def _write_raw_response(config: PolygonProbeConfig, check: PolygonCheck, payload: dict) -> Path:
    raw_dir = config.evaluation_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{check.event_id}_{check.capability}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_probe_summary(config: PolygonProbeConfig, results: list[dict[str, object]]) -> None:
    path = config.evaluation_dir / "polygon_probe_summary.csv"
    fields = ["event_id", "symbol", "capability", "status", "http_status", "result_count", "fields_preview", "payload_sha256", "raw_response_path"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def _update_artifacts(config: PolygonProbeConfig, results: list[dict[str, object]]) -> None:
    _update_manifest(config)
    _update_raw_manifest(config, results)
    _update_event_audit(config, results)
    _update_summary(config, results)
    _update_snapshot_hashes(config)


def _update_manifest(config: PolygonProbeConfig) -> None:
    path = config.evaluation_dir / "provider_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["provider_query_executed"] = True
    manifest["actual_query_cost_usd"] = 0
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _update_raw_manifest(config: PolygonProbeConfig, results: list[dict[str, object]]) -> None:
    path = config.evaluation_dir / "raw_responses_manifest.csv"
    rows = _read_csv_dicts(path)
    by_event = {str(result["event_id"]): result for result in results}
    for row in rows:
        result = by_event.get(row["event_id"])
        if result:
            row["path"] = str(result["raw_response_path"])
            row["sha256"] = str(result["payload_sha256"])
    _write_csv_dicts(path, rows, ["event_id", "path", "sha256"])


def _update_event_audit(config: PolygonProbeConfig, results: list[dict[str, object]]) -> None:
    path = config.evaluation_dir / "provider_event_audit_table.csv"
    rows = _read_csv_dicts(path)
    by_event: dict[str, list[dict[str, object]]] = {}
    for result in results:
        by_event.setdefault(str(result["event_id"]), []).append(result)
    for row in rows:
        event_results = by_event.get(row["event_id"], [])
        passed = [r for r in event_results if r["status"] == "pass"]
        if not event_results:
            continue
        row["provider_symbol_resolves"] = "yes" if passed else "unclear"
        row["historical_identifier_stable"] = "partial" if passed else "unclear"
        row["event_window_available"] = "yes" if any("aggregate" in str(r["capability"]) and r["result_count"] for r in passed) else "not_tested"
        row["raw_ohlcv_available"] = "yes" if any("aggregate" in str(r["capability"]) and r["result_count"] for r in passed) else "not_tested"
        row["adjusted_ohlcv_available"] = "partial" if any("aggregate" in str(r["capability"]) and r["result_count"] for r in passed) else "not_tested"
        row["corporate_action_metadata_available"] = "yes" if any("split" in str(r["capability"]) or "dividend" in str(r["capability"]) for r in passed) else "not_tested"
        row["halt_or_suspension_visible"] = "not_tested"
        row["delisted_history_available"] = "partial" if any("delisted" in str(r["capability"]) for r in passed) else "not_tested"
        row["point_in_time_universe_supported"] = "unclear"
        row["licensing_allows_research_storage"] = "unclear"
        row["verdict"] = "caveat" if passed else "fail"
        row["notes"] = "POLYGON_FREE_MICRO_PROBE_EXECUTED_NO_RAW_RETENTION"
    _write_csv_dicts(path, rows, list(rows[0].keys()))


def _update_summary(config: PolygonProbeConfig, results: list[dict[str, object]]) -> None:
    path = config.evaluation_dir / "provider_evaluation_summary.md"
    current = path.read_text(encoding="utf-8")
    passed = sum(1 for result in results if result["status"] == "pass")
    timestamp = datetime.now(UTC).isoformat()
    addition = f"\n## Polygon free micro-probe update\n\n```text\nPROVIDER_QUERY_EXECUTED\nchecks_executed: {len(results)}\nchecks_passed: {passed}\nexecuted_at_utc: {timestamp}\nraw_response_retention: disabled\nrate_limit_control: sleep between calls\n```\n"
    if "## Polygon free micro-probe update" not in current:
        path.write_text(current.rstrip() + "\n" + addition, encoding="utf-8")


def _update_snapshot_hashes(config: PolygonProbeConfig) -> None:
    files = [
        "provider_manifest.json",
        "provider_requirement_table.csv",
        "provider_event_audit_table.csv",
        "license_notes.md",
        "query_cost_estimate.md",
        "raw_responses_manifest.csv",
        "provider_evaluation_summary.md",
        "polygon_probe_summary.csv",
    ]
    path = config.evaluation_dir / "snapshot_hashes.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256"])
        writer.writeheader()
        for name in files:
            file_path = config.evaluation_dir / name
            writer.writerow({"path": name, "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()})


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv_dicts(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _sha256_json(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _fingerprint_secret(secret: str) -> str:
    if not secret:
        return "missing"
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:12]}"


if __name__ == "__main__":
    raise SystemExit(main())
