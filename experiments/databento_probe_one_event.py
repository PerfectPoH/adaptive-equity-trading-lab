from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import dotenv_values


DEFAULT_EVALUATION_DIR = Path("experiments/provider_evaluations/databento_equities_historical_20260517")
DEFAULT_EVENT_ID = "DPE-006"
DEFAULT_DATASET = "EQUS.MINI"
DEFAULT_SCHEMA = "trades"
DEFAULT_SYMBOL = "FSR"
DEFAULT_START = "2024-03-20T14:30"
DEFAULT_END = "2024-03-20T14:35"
DEFAULT_LIMIT = 10
API_KEY_ENV_NAME = "DATABENTO_API_KEY"


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
    metadata_smoke_test: bool
    dataset_diagnostics: bool
    retain_raw_response: bool
    api_key_source: str
    env_file: Path


class ApiKeySourceError(RuntimeError):
    def __init__(self, code: str, detail: str, diagnostics: dict[str, str | bool | int]) -> None:
        super().__init__(detail)
        self.code = code
        self.diagnostics = diagnostics


def main(argv: list[str] | None = None) -> int:
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
        metadata_smoke_test=args.metadata_smoke_test,
        dataset_diagnostics=args.dataset_diagnostics,
        retain_raw_response=args.retain_raw_response,
        api_key_source=args.api_key_source,
        env_file=Path(args.env_file),
    )
    try:
        api_key, key_diagnostics = _resolve_databento_api_key(config.api_key_source, config.env_file)
    except ApiKeySourceError as exc:
        _write_error_artifact(config, exc.code, str(exc), exc.diagnostics)
        print(f"DATABENTO_KEY_ERROR:{exc.code}", file=sys.stderr)
        return 2
    if not api_key:
        _write_error_artifact(config, "DATABENTO_API_KEY_MISSING", "No Databento API key found.", key_diagnostics)
        print("DATABENTO_API_KEY_MISSING", file=sys.stderr)
        return 2

    if config.dry_run:
        print(json.dumps(_redacted_request_summary(config, status="dry_run", key_diagnostics=key_diagnostics), indent=2, sort_keys=True))
        return 0

    if config.metadata_smoke_test:
        try:
            datasets = _list_databento_datasets(api_key)
        except ImportError:
            _write_error_artifact(config, "DATABENTO_PACKAGE_MISSING", "Install databento in the active Python environment.", key_diagnostics)
            print("DATABENTO_PACKAGE_MISSING", file=sys.stderr)
            return 4
        except Exception as exc:
            _write_error_artifact(config, exc.__class__.__name__, str(exc), key_diagnostics)
            print(f"DATABENTO_ERROR:{exc.__class__.__name__}", file=sys.stderr)
            return 5
        status = "metadata_smoke_test_pass" if config.dataset in datasets else "metadata_smoke_test_dataset_missing"
        print(
            json.dumps(
                {
                    "status": status,
                    "dataset": config.dataset,
                    "dataset_available": config.dataset in datasets,
                    "dataset_count": len(datasets),
                    "api_key": "REDACTED",
                    **key_diagnostics,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if config.dataset in datasets else 6

    if config.dataset_diagnostics:
        try:
            diagnostics = _run_dataset_diagnostics(config, api_key)
        except ImportError:
            _write_error_artifact(config, "DATABENTO_PACKAGE_MISSING", "Install databento in the active Python environment.", key_diagnostics)
            print("DATABENTO_PACKAGE_MISSING", file=sys.stderr)
            return 4
        except Exception as exc:
            _write_error_artifact(config, exc.__class__.__name__, str(exc), key_diagnostics)
            print(f"DATABENTO_ERROR:{exc.__class__.__name__}", file=sys.stderr)
            return 5
        output = {
            "status": "dataset_diagnostics_pass",
            "api_key": "REDACTED",
            **key_diagnostics,
            **diagnostics,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0

    if not config.evaluation_dir.exists():
        print(f"EVALUATION_DIR_MISSING: {config.evaluation_dir}", file=sys.stderr)
        return 3

    try:
        response = _fetch_databento_records(config, api_key)
    except ImportError:
        _write_error_artifact(config, "DATABENTO_PACKAGE_MISSING", "Install databento in the active Python environment.", key_diagnostics)
        print("DATABENTO_PACKAGE_MISSING", file=sys.stderr)
        return 4
    except Exception as exc:
        _write_error_artifact(config, exc.__class__.__name__, str(exc), key_diagnostics)
        print(f"DATABENTO_ERROR:{exc.__class__.__name__}", file=sys.stderr)
        return 5

    raw_path = _write_raw_response(config, response) if config.retain_raw_response else None
    _update_raw_response_manifest(config, raw_path, response)
    _update_provider_event_audit_table(config, response)
    _update_provider_manifest(config)
    _update_provider_evaluation_summary(config, raw_path, response)
    print(json.dumps(_redacted_request_summary(config, status="pass", records=len(response), key_diagnostics=key_diagnostics), indent=2, sort_keys=True))
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
    parser.add_argument("--metadata-smoke-test", action="store_true")
    parser.add_argument("--dataset-diagnostics", action="store_true")
    parser.add_argument("--retain-raw-response", action="store_true")
    parser.add_argument("--api-key-source", choices=["auto", "environment", "env-file"], default="auto")
    parser.add_argument("--env-file", default=".env")
    return parser


def _resolve_databento_api_key(api_key_source: str, env_file: Path) -> tuple[str, dict[str, str | bool | int]]:
    env_key = os.environ.get(API_KEY_ENV_NAME, "")
    file_key = ""
    if env_file.exists():
        file_key = str(dotenv_values(env_file).get(API_KEY_ENV_NAME) or "")

    diagnostics = _api_key_diagnostics(
        requested_source=api_key_source,
        resolved_source="missing",
        env_file=env_file,
        env_key=env_key,
        file_key=file_key,
        selected_key="",
    )

    if api_key_source == "environment":
        return env_key, _api_key_diagnostics(api_key_source, "environment", env_file, env_key, file_key, env_key)
    if api_key_source == "env-file":
        return file_key, _api_key_diagnostics(api_key_source, "env-file", env_file, env_key, file_key, file_key)

    if env_key and file_key and env_key != file_key:
        raise ApiKeySourceError(
            "DATABENTO_API_KEY_SOURCE_CONFLICT",
            "Both process environment and env file define DATABENTO_API_KEY with different redacted fingerprints. "
            "Rerun with --api-key-source environment or --api-key-source env-file.",
            _api_key_diagnostics(api_key_source, "conflict", env_file, env_key, file_key, ""),
        )
    if env_key:
        return env_key, _api_key_diagnostics(api_key_source, "environment", env_file, env_key, file_key, env_key)
    if file_key:
        return file_key, _api_key_diagnostics(api_key_source, "env-file", env_file, env_key, file_key, file_key)
    return "", diagnostics


def _api_key_diagnostics(
    requested_source: str,
    resolved_source: str,
    env_file: Path,
    env_key: str,
    file_key: str,
    selected_key: str,
) -> dict[str, str | bool | int]:
    return {
        "api_key": "REDACTED",
        "api_key_source_requested": requested_source,
        "api_key_source_resolved": resolved_source,
        "api_key_fingerprint": _fingerprint_secret(selected_key),
        "environment_key_present": bool(env_key),
        "environment_key_fingerprint": _fingerprint_secret(env_key),
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "env_file_key_present": bool(file_key),
        "env_file_key_fingerprint": _fingerprint_secret(file_key),
    }


def _list_databento_datasets(api_key: str) -> list[str]:
    import databento as db

    client = db.Historical(api_key)
    return list(client.metadata.list_datasets())


def _run_dataset_diagnostics(config: DatabentoProbeConfig, api_key: str) -> dict[str, object]:
    import databento as db

    client = db.Historical(api_key)
    datasets = list(client.metadata.list_datasets())
    schemas = list(client.metadata.list_schemas(config.dataset))
    fields = client.metadata.list_fields(config.schema, "dbn")
    cost = client.metadata.get_cost(
        dataset=config.dataset,
        schema=config.schema,
        symbols=config.symbol,
        start=config.start,
        end=config.end,
        limit=config.limit,
    )
    record_count = client.metadata.get_record_count(
        dataset=config.dataset,
        schema=config.schema,
        symbols=config.symbol,
        start=config.start,
        end=config.end,
        limit=config.limit,
    )
    symbology = client.symbology.resolve(
        dataset=config.dataset,
        symbols=config.symbol,
        stype_in="raw_symbol",
        stype_out="instrument_id",
        start_date=config.start[:10],
        end_date=_next_date(config.end[:10]),
    )
    return {
        "dataset": config.dataset,
        "dataset_available": config.dataset in datasets,
        "dataset_count": len(datasets),
        "schema": config.schema,
        "schema_available": config.schema in schemas,
        "schemas": schemas,
        "field_count": len(fields),
        "fields_preview": fields[:20],
        "symbol": config.symbol,
        "start": config.start,
        "end": config.end,
        "limit": config.limit,
        "estimated_cost_usd": cost,
        "record_count": record_count,
        "symbology_result": symbology,
    }


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


def _next_date(date_text: str) -> str:
    return (datetime.fromisoformat(date_text) + timedelta(days=1)).date().isoformat()


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
    raw_path_text = str(raw_path).replace("\\", "/") if raw_path else "RAW_RESPONSE_RETENTION_NOT_ENABLED"
    addition = f"\n## One-event micro-probe update\n\n```text\nPROVIDER_QUERY_EXECUTED\nevent_id: {config.event_id}\ndataset: {config.dataset}\nschema: {config.schema}\nsymbol: {config.symbol}\nstart: {config.start}\nend: {config.end}\nlimit: {config.limit}\nrecords_returned: {len(response)}\nexecuted_at_utc: {timestamp}\nraw_response_path: {raw_path_text}\n```\n"
    if "## One-event micro-probe update" not in current:
        path.write_text(current.rstrip() + "\n" + addition, encoding="utf-8")


def _write_error_artifact(
    config: DatabentoProbeConfig,
    code: str,
    detail: str,
    key_diagnostics: dict[str, str | bool | int] | None = None,
) -> None:
    config.evaluation_dir.mkdir(parents=True, exist_ok=True)
    path = config.evaluation_dir / f"{config.event_id}_databento_probe_error.json"
    payload = {
        "event_id": config.event_id,
        "dataset": config.dataset,
        "schema": config.schema,
        "symbol": config.symbol,
        "code": code,
        "detail": detail,
        "api_key": "REDACTED",
        **(key_diagnostics or {}),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _redacted_request_summary(
    config: DatabentoProbeConfig,
    status: str,
    records: int | None = None,
    key_diagnostics: dict[str, str | bool | int] | None = None,
) -> dict[str, str | int | bool | None]:
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
        **(key_diagnostics or {}),
    }


def _fingerprint_secret(secret: str) -> str:
    if not secret:
        return ""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


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
