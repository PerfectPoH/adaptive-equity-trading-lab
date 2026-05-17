from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_EVALUATION_DIR = Path("experiments/provider_evaluations/intrinio_starter_event_panel_20260517")
DEFAULT_EVENT_ID = "DPE-006"
DEFAULT_IDENTIFIER = "FSR"
DEFAULT_START_DATE = "2024-03-20"
DEFAULT_END_DATE = "2024-03-28"
INTRINIO_BASE_URL = "https://api-v2.intrinio.com"


@dataclass(frozen=True)
class IntrinioProbeConfig:
    evaluation_dir: Path
    event_id: str
    identifier: str
    start_date: str
    end_date: str
    dry_run: bool
    retain_raw_response: bool
    auth_method: str


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = IntrinioProbeConfig(
        evaluation_dir=Path(args.evaluation_dir),
        event_id=args.event_id,
        identifier=args.identifier,
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=args.dry_run,
        retain_raw_response=args.retain_raw_response,
        auth_method=args.auth_method,
    )
    api_key = os.environ.get("INTRINIO_API_KEY")
    if not api_key:
        print("INTRINIO_API_KEY_MISSING", file=sys.stderr)
        return 2

    if config.dry_run:
        endpoint = _historical_prices_endpoint(config, api_key="REDACTED", include_api_key=config.auth_method == "url_param")
        print(json.dumps({"status": "dry_run", "endpoint": endpoint, "api_key": "REDACTED", "auth_method": config.auth_method}, indent=2, sort_keys=True))
        return 0

    if not config.evaluation_dir.exists():
        print(f"EVALUATION_DIR_MISSING: {config.evaluation_dir}", file=sys.stderr)
        return 3

    try:
        response = _fetch_json(config, api_key)
    except HTTPError as exc:
        _write_error_artifact(config, f"HTTP_ERROR_{exc.code}", exc.reason)
        print(f"HTTP_ERROR_{exc.code}", file=sys.stderr)
        return 4
    except URLError as exc:
        _write_error_artifact(config, "URL_ERROR", str(exc.reason))
        print("URL_ERROR", file=sys.stderr)
        return 5

    raw_path = _write_raw_response(config, response) if config.retain_raw_response else None
    _update_raw_response_manifest(config, raw_path, response)
    _update_provider_event_audit_table(config, response)
    _update_provider_manifest(config)
    _update_provider_evaluation_summary(config, raw_path)
    print(json.dumps({"status": "pass", "event_id": config.event_id, "identifier": config.identifier, "api_key": "REDACTED"}, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one Intrinio provider-evaluation probe for one frozen event.")
    parser.add_argument("--evaluation-dir", default=str(DEFAULT_EVALUATION_DIR))
    parser.add_argument("--event-id", default=DEFAULT_EVENT_ID)
    parser.add_argument("--identifier", default=DEFAULT_IDENTIFIER)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retain-raw-response", action="store_true")
    parser.add_argument("--auth-method", choices=["url_param", "bearer"], default="url_param")
    return parser


def _historical_prices_endpoint(config: IntrinioProbeConfig, api_key: str, include_api_key: bool) -> str:
    query_params = {
            "start_date": config.start_date,
            "end_date": config.end_date,
            "frequency": "daily",
            "page_size": 100,
    }
    if include_api_key:
        query_params["api_key"] = api_key
    query = urlencode(query_params)
    return f"{INTRINIO_BASE_URL}/securities/{config.identifier}/prices?{query}"


def _fetch_json(config: IntrinioProbeConfig, api_key: str) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-provider-eval"}
    if config.auth_method == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    url = _historical_prices_endpoint(config, api_key=api_key, include_api_key=config.auth_method == "url_param")
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _write_raw_response(config: IntrinioProbeConfig, response: dict) -> Path:
    raw_dir = config.evaluation_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{config.event_id}_intrinio_historical_prices.json"
    path.write_text(json.dumps(response, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _update_raw_response_manifest(config: IntrinioProbeConfig, raw_path: Path | None, response: dict) -> None:
    manifest_path = config.evaluation_dir / "raw_responses_manifest.csv"
    rows = _read_csv_dicts(manifest_path)
    digest = _sha256_json(response)
    for row in rows:
        if row["event_id"] == config.event_id:
            row["path"] = str(raw_path).replace("\\", "/") if raw_path else "RAW_RESPONSE_RETENTION_NOT_ENABLED"
            row["sha256"] = digest
    _write_csv_dicts(manifest_path, rows, ["event_id", "path", "sha256"])


def _update_provider_event_audit_table(config: IntrinioProbeConfig, response: dict) -> None:
    path = config.evaluation_dir / "provider_event_audit_table.csv"
    rows = _read_csv_dicts(path)
    prices = response.get("stock_prices")
    has_prices = isinstance(prices, list) and len(prices) > 0
    for row in rows:
        if row["event_id"] == config.event_id:
            row["provider_symbol_resolves"] = "yes" if has_prices else "unclear"
            row["historical_identifier_stable"] = "unclear"
            row["event_window_available"] = "yes" if has_prices else "unclear"
            row["raw_ohlcv_available"] = "yes" if has_prices else "unclear"
            row["adjusted_ohlcv_available"] = "unclear"
            row["corporate_action_metadata_available"] = "not_tested"
            row["halt_or_suspension_visible"] = "not_tested"
            row["delisted_history_available"] = "not_tested"
            row["point_in_time_universe_supported"] = "not_tested"
            row["licensing_allows_research_storage"] = "unclear"
            row["verdict"] = "caveat"
            row["notes"] = "INTRINIO_ONE_EVENT_PRICE_PROBE_EXECUTED_LIMITED_SCOPE"
    _write_csv_dicts(path, rows, list(rows[0].keys()))


def _update_provider_manifest(config: IntrinioProbeConfig) -> None:
    path = config.evaluation_dir / "provider_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["provider_query_executed"] = True
    manifest["actual_query_cost_usd"] = 0
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _update_provider_evaluation_summary(config: IntrinioProbeConfig, raw_path: Path | None) -> None:
    path = config.evaluation_dir / "provider_evaluation_summary.md"
    current = path.read_text(encoding="utf-8")
    timestamp = datetime.now(UTC).isoformat()
    addition = f"\n## One-event probe update\n\n```text\nPROVIDER_QUERY_EXECUTED\nevent_id: {config.event_id}\nidentifier: {config.identifier}\nstart_date: {config.start_date}\nend_date: {config.end_date}\nexecuted_at_utc: {timestamp}\nraw_response_path: {str(raw_path).replace('\\\\', '/') if raw_path else 'RAW_RESPONSE_RETENTION_NOT_ENABLED'}\nactual_query_cost_usd: 0\n```\n"
    if "## One-event probe update" not in current:
        path.write_text(current.rstrip() + "\n" + addition, encoding="utf-8")


def _write_error_artifact(config: IntrinioProbeConfig, code: str, detail: str) -> None:
    path = config.evaluation_dir / f"{config.event_id}_intrinio_probe_error.json"
    payload = {"event_id": config.event_id, "identifier": config.identifier, "code": code, "detail": detail, "api_key": "REDACTED"}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _sha256_json(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv_dicts(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
