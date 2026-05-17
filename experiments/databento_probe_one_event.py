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

from dotenv import load_dotenv


DEFAULT_EVALUATION_DIR = Path("experiments/provider_evaluations/databento_equities_historical_20260517")
DEFAULT_EVENT_ID = "DPE-006"
DEFAULT_DATASET = "EQUS.MINI"
DEFAULT_SCHEMA = "trades"
DEFAULT_SYMBOL = "FSR"
DEFAULT_START = "2024-03-20T14:30"
DEFAULT_END = "2024-03-20T14:35"
DEFAULT_LIMIT = 10


@dataclass(frozen=True)
class DatabentoProbeConfig:
    evaluation_dir: Path
    event_id: str
    dataset: str
    schema: str
    symbol: str
    start: str
    end: str
    limit: int
    dry_run: bool
    retain_raw_response: bool


def main(argv: list[str] | None = None) -> int:
    load_dotenv(Path.cwd() / ".env")
    args = _build_parser().parse_args(argv)
    config = DatabentoProbeConfig(
        evaluation_dir=Path(args.evaluation_dir),
        event_id=args.event_id,
        dataset=args.dataset,
        schema=args.schema,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        limit=args.limit,
        dry_run=args.dry_run,
        retain_raw_response=args.retain_raw_response,
    )
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print("DATABENTO_API_KEY_MISSING", file=sys.stderr)
        return 2

    if config.dry_run:
        print(json.dumps(_redacted_request_summary(config, status="dry_run"), indent=2, sort_keys=True))
        return 0

    if not config.evaluation_dir.exists():
        print(f"EVALUATION_DIR_MISSING: {config.evaluation_dir}", file=sys.stderr)
        return 3

    try:
        response = _fetch_databento_records(config, api_key)
    except ImportError:
        _write_error_artifact(config, "DATABENTO_PACKAGE_MISSING", "Install databento in the active Python environment.")
        print("DATABENTO_PACKAGE_MISSING", file=sys.stderr)
        return 4
    except Exception as exc:
        _write_error_artifact(config, exc.__class__.__name__, str(exc))
        print(f"DATABENTO_ERROR:{exc.__class__.__name__}", file=sys.stderr)
        return 5

    raw_path = _write_raw_response(config, response) if config.retain_raw_response else None
    _update_raw_response_manifest(config, raw_path, response)
    _update_provider_event_audit_table(config, response)
    _update_provider_manifest(config)
    _update_provider_evaluation_summary(config, raw_path, response)
    print(json.dumps(_redacted_request_summary(config, status="pass", records=len(response)), indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one Databento provider-evaluation micro-probe for one event.")
    parser.add_argument("--evaluation-dir", default=str(DEFAULT_EVALUATION_DIR))
    parser.add_argument("--event-id", default=DEFAULT_EVENT_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retain-raw-response", action="store_true")
    return parser


def _fetch_databento_records(config: DatabentoProbeConfig, api_key: str) -> list[dict[str, str]]:
    import databento as db

    client = db.Historical(api_key)
    data = client.timeseries.get_range(
        dataset=config.dataset,
        schema=config.schema,
        symbols=config.symbol,
        start=config.start,
        end=config.end,
        limit=config.limit,
    )
    frame = data.to_df()
    if frame is None or frame.empty:
        return []
    return json.loads(frame.reset_index().astype(str).to_json(orient="records"))


def _write_raw_response(config: DatabentoProbeConfig, response: list[dict[str, str]]) -> Path:
    raw_dir = config.evaluation_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{config.event_id}_databento_{config.dataset}_{config.schema}_{config.symbol}.json"
    path.write_text(json.dumps(response, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _update_raw_response_manifest(config: DatabentoProbeConfig, raw_path: Path | None, response: list[dict[str, str]]) -> None:
    manifest_path = config.evaluation_dir / "raw_responses_manifest.csv"
    rows = _read_csv_dicts(manifest_path)
    digest = _sha256_json(response)
    for row in rows:
        if row["event_id"] == config.event_id:
            row["path"] = str(raw_path).replace("\\", "/") if raw_path else "RAW_RESPONSE_RETENTION_NOT_ENABLED"
            row["sha256"] = digest
    _write_csv_dicts(manifest_path, rows, ["event_id", "path", "sha256"])


def _update_provider_event_audit_table(config: DatabentoProbeConfig, response: list[dict[str, str]]) -> None:
    path = config.evaluation_dir / "provider_event_audit_table.csv"
    rows = _read_csv_dicts(path)
    has_records = len(response) > 0
    for row in rows:
        if row["event_id"] == config.event_id:
            row["provider_symbol_resolves"] = "yes" if has_records else "unclear"
            row["historical_identifier_stable"] = "unclear"
            row["event_window_available"] = "yes" if has_records else "unclear"
            row["raw_ohlcv_available"] = "not_tested"
            row["adjusted_ohlcv_available"] = "not_tested"
            row["corporate_action_metadata_available"] = "not_tested"
            row["halt_or_suspension_visible"] = "not_tested"
            row["delisted_history_available"] = "not_tested"
            row["point_in_time_universe_supported"] = "not_tested"
            row["licensing_allows_research_storage"] = "unclear"
            row["verdict"] = "caveat"
            row["notes"] = "DATABENTO_ONE_EVENT_MICRO_PROBE_EXECUTED_LIMITED_SCOPE"
    _write_csv_dicts(path, rows, list(rows[0].keys()))


def _update_provider_manifest(config: DatabentoProbeConfig) -> None:
    path = config.evaluation_dir / "provider_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["provider_query_executed"] = True
    manifest["query_budget_estimate_usd"] = 125
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _update_provider_evaluation_summary(config: DatabentoProbeConfig, raw_path: Path | None, response: list[dict[str, str]]) -> None:
    path = config.evaluation_dir / "provider_evaluation_summary.md"
    current = path.read_text(encoding="utf-8")
    timestamp = datetime.now(UTC).isoformat()
    addition = f"\n## One-event micro-probe update\n\n```text\nPROVIDER_QUERY_EXECUTED\nevent_id: {config.event_id}\ndataset: {config.dataset}\nschema: {config.schema}\nsymbol: {config.symbol}\nstart: {config.start}\nend: {config.end}\nlimit: {config.limit}\nrecords_returned: {len(response)}\nexecuted_at_utc: {timestamp}\nraw_response_path: {str(raw_path).replace('\\\\', '/') if raw_path else 'RAW_RESPONSE_RETENTION_NOT_ENABLED'}\n```\n"
    if "## One-event micro-probe update" not in current:
        path.write_text(current.rstrip() + "\n" + addition, encoding="utf-8")


def _write_error_artifact(config: DatabentoProbeConfig, code: str, detail: str) -> None:
    path = config.evaluation_dir / f"{config.event_id}_databento_probe_error.json"
    payload = {"event_id": config.event_id, "dataset": config.dataset, "schema": config.schema, "symbol": config.symbol, "code": code, "detail": detail, "api_key": "REDACTED"}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _redacted_request_summary(config: DatabentoProbeConfig, status: str, records: int | None = None) -> dict[str, str | int | None]:
    return {
        "status": status,
        "event_id": config.event_id,
        "dataset": config.dataset,
        "schema": config.schema,
        "symbol": config.symbol,
        "start": config.start,
        "end": config.end,
        "limit": config.limit,
        "records": records,
        "api_key": "REDACTED",
    }


def _sha256_json(payload: list[dict[str, str]]) -> str:
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
