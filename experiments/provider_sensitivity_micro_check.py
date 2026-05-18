from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
from dotenv import dotenv_values


DEFAULT_SPEC_DIR = Path("experiments/provider_sensitivity/provider_sensitivity_test_spec_20260518")
DATABENTO_ENV = "DATABENTO_API_KEY"
POLYGON_ENV = "POLYGON_API_KEY"
POLYGON_BASE_URL = "https://api.polygon.io"


@dataclass(frozen=True)
class SensitivityConfig:
    spec_dir: Path
    env_file: Path
    api_key_source: str
    sleep_seconds: float
    max_candidates: int
    candidates_file: str
    output_prefix: str
    skip_polygon: bool


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = SensitivityConfig(
        spec_dir=Path(args.spec_dir),
        env_file=Path(args.env_file),
        api_key_source=args.api_key_source,
        sleep_seconds=args.sleep_seconds,
        max_candidates=args.max_candidates,
        candidates_file=args.candidates_file,
        output_prefix=args.output_prefix,
        skip_polygon=args.skip_polygon,
    )
    databento_key = _resolve_key(DATABENTO_ENV, config)
    polygon_key = _resolve_key(POLYGON_ENV, config)
    if not databento_key:
        print("DATABENTO_API_KEY_MISSING", file=sys.stderr)
        return 2
    if not polygon_key and not config.skip_polygon:
        print("POLYGON_API_KEY_MISSING", file=sys.stderr)
        return 2
    candidates = _read_candidates(config.spec_dir, config.candidates_file)[: config.max_candidates]
    if not candidates:
        print("NO_CANDIDATES", file=sys.stderr)
        return 3
    results = []
    for index, candidate in enumerate(candidates):
        if index > 0:
            time.sleep(config.sleep_seconds)
        results.append(_check_candidate(candidate, databento_key, polygon_key, skip_polygon=config.skip_polygon))
        _write_results(config.spec_dir, results, config.output_prefix)
        print(
            json.dumps(
                {
                    "status": "progress",
                    "completed": len(results),
                    "total": len(candidates),
                    "symbol": candidate.get("symbol", ""),
                    "raw_retention": "disabled",
                },
                sort_keys=True,
            ),
            flush=True,
        )
    _write_results(config.spec_dir, results, config.output_prefix)
    print(json.dumps({"status": "completed", "candidates_checked": len(results), "raw_retention": "disabled", "results": results}, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run controlled provider-sensitivity micro-checks without raw retention.")
    parser.add_argument("--spec-dir", default=str(DEFAULT_SPEC_DIR))
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--api-key-source", choices=["env-file", "environment"], default="env-file")
    parser.add_argument("--sleep-seconds", type=float, default=13.0)
    parser.add_argument("--max-candidates", type=int, default=4)
    parser.add_argument("--candidates-file", default="overlap_selection_candidates.csv")
    parser.add_argument("--output-prefix", default="provider_sensitivity_micro_check")
    parser.add_argument("--skip-polygon", action="store_true")
    return parser


def _resolve_key(name: str, config: SensitivityConfig) -> str:
    if config.api_key_source == "environment":
        return os.environ.get(name, "")
    if not config.env_file.exists():
        return ""
    return str(dotenv_values(config.env_file).get(name) or "")


def _read_candidates(spec_dir: Path, candidates_file: str) -> list[dict[str, str]]:
    path = spec_dir / candidates_file
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _check_candidate(candidate: dict[str, str], databento_key: str, polygon_key: str, *, skip_polygon: bool) -> dict[str, object]:
    y_entry = _to_float(candidate.get("entry_price"))
    y_exit = _to_float(candidate.get("exit_price"))
    y_return = _to_float(candidate.get("return_pct"))
    db_result = _databento_ohlcv_summary(candidate, databento_key)
    polygon_result = _polygon_ticker_summary(candidate, polygon_key) if not skip_polygon else _polygon_skipped_summary()
    db_entry_open = _to_float(db_result.get("entry_date_open"))
    db_exit_close = _to_float(db_result.get("exit_date_close"))
    db_return = None
    if db_entry_open and db_exit_close:
        db_return = (db_exit_close / db_entry_open) - 1
    return_delta = None if db_return is None or y_return is None else db_return - y_return
    entry_delta_pct = None if db_entry_open is None or y_entry is None else (db_entry_open / y_entry) - 1
    exit_delta_pct = None if db_exit_close is None or y_exit is None else (db_exit_close / y_exit) - 1
    sensitivity = _classify_sensitivity(db_result, polygon_result, entry_delta_pct, exit_delta_pct, return_delta)
    return {
        "reference_run": candidate.get("reference_run", ""),
        "symbol": candidate.get("symbol", ""),
        "signal_date": candidate.get("signal_date", ""),
        "entry_date": candidate.get("entry_date", ""),
        "exit_date": candidate.get("exit_date", ""),
        "yfinance_entry_price": y_entry,
        "yfinance_exit_price": y_exit,
        "yfinance_return_pct": y_return,
        **db_result,
        **polygon_result,
        "entry_delta_pct": entry_delta_pct,
        "exit_delta_pct": exit_delta_pct,
        "return_delta": return_delta,
        "sensitivity_class": sensitivity,
        "raw_response_path": "RAW_RESPONSE_RETENTION_NOT_ENABLED",
    }


def _databento_ohlcv_summary(candidate: dict[str, str], api_key: str) -> dict[str, object]:
    try:
        import databento as db

        client = db.Historical(api_key)
        symbol = str(candidate["symbol"])
        start = str(candidate["signal_date"])
        end = _next_day(str(candidate["exit_date"]))
        data = client.timeseries.get_range(dataset="EQUS.MINI", schema="ohlcv-1d", symbols=symbol, start=start, end=end)
        frame = data.to_df()
        if frame is None or frame.empty:
            return {"databento_status": "empty", "databento_rows": 0, "entry_date_open": None, "exit_date_close": None, "databento_payload_sha256": _sha256_json({"empty": True})}
        normalized = frame.reset_index().astype(str)
        entry_row = _date_row(normalized, str(candidate["entry_date"]))
        exit_row = _date_row(normalized, str(candidate["exit_date"]))
        digest_payload = normalized.head(20).to_dict(orient="records")
        return {
            "databento_status": "pass",
            "databento_rows": int(len(frame)),
            "entry_date_open": _record_value(entry_row, "open"),
            "exit_date_close": _record_value(exit_row, "close"),
            "databento_fields": "|".join(map(str, normalized.columns[:20])),
            "databento_payload_sha256": _sha256_json(digest_payload),
        }
    except Exception as exc:
        return {"databento_status": f"error:{exc.__class__.__name__}", "databento_rows": 0, "entry_date_open": None, "exit_date_close": None, "databento_fields": "", "databento_payload_sha256": _sha256_json({"error": exc.__class__.__name__})}


def _polygon_ticker_summary(candidate: dict[str, str], api_key: str) -> dict[str, object]:
    symbol = str(candidate["symbol"])
    date = str(candidate["signal_date"])
    params = urlencode({"date": date, "apiKey": api_key})
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{symbol}?{params}"
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab-provider-sensitivity"})
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        results = payload.get("results") if isinstance(payload, dict) else None
        if isinstance(results, dict):
            return {
                "polygon_status": str(payload.get("status", "unknown")),
                "polygon_result_count": 1,
                "polygon_active": str(results.get("active", "")),
                "polygon_primary_exchange": str(results.get("primary_exchange", "")),
                "polygon_payload_sha256": _sha256_json({k: results.get(k) for k in sorted(results)[:20]}),
            }
        return {"polygon_status": "empty", "polygon_result_count": 0, "polygon_active": "", "polygon_primary_exchange": "", "polygon_payload_sha256": _sha256_json({"empty": True})}
    except HTTPError as exc:
        return {"polygon_status": f"HTTP_ERROR_{exc.code}", "polygon_result_count": 0, "polygon_active": "", "polygon_primary_exchange": "", "polygon_payload_sha256": _sha256_json({"error": exc.code})}
    except URLError as exc:
        return {"polygon_status": "URL_ERROR", "polygon_result_count": 0, "polygon_active": "", "polygon_primary_exchange": "", "polygon_payload_sha256": _sha256_json({"error": str(exc.reason)})}


def _polygon_skipped_summary() -> dict[str, object]:
    return {
        "polygon_status": "skipped",
        "polygon_result_count": 0,
        "polygon_active": "",
        "polygon_primary_exchange": "",
        "polygon_payload_sha256": _sha256_json({"skipped": True}),
    }


def _classify_sensitivity(db_result: dict[str, object], polygon_result: dict[str, object], entry_delta: float | None, exit_delta: float | None, return_delta: float | None) -> str:
    if db_result.get("databento_status") != "pass":
        return "provider_unavailable"
    if polygon_result.get("polygon_status") != "skipped" and polygon_result.get("polygon_result_count") == 0:
        return "reference_unavailable_caveat"
    deltas = [abs(value) for value in (entry_delta, exit_delta, return_delta) if value is not None]
    if not deltas:
        return "insufficient_comparable_fields"
    if max(deltas) > 0.05:
        return "material_price_or_return_delta"
    if max(deltas) > 0.01:
        return "minor_price_or_return_delta"
    return "provider_stable_for_selected_fields"


def _date_row(frame: pd.DataFrame, date_text: str) -> dict[str, str] | None:
    for _, row in frame.iterrows():
        row_text = " ".join(str(value) for value in row.values)
        if date_text in row_text:
            return row.to_dict()
    return None


def _record_value(row: dict[str, str] | None, key: str) -> float | None:
    if not row:
        return None
    for candidate_key, value in row.items():
        if str(candidate_key).lower().endswith(key):
            return _to_float(value)
    return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _next_day(date_text: str) -> str:
    return (pd.Timestamp(date_text) + pd.Timedelta(days=1)).date().isoformat()


def _write_results(spec_dir: Path, results: list[dict[str, object]], output_prefix: str) -> None:
    path = spec_dir / f"{output_prefix}_results.csv"
    fields = [
        "reference_run",
        "symbol",
        "signal_date",
        "entry_date",
        "exit_date",
        "yfinance_entry_price",
        "yfinance_exit_price",
        "yfinance_return_pct",
        "databento_status",
        "databento_rows",
        "entry_date_open",
        "exit_date_close",
        "databento_fields",
        "databento_payload_sha256",
        "polygon_status",
        "polygon_result_count",
        "polygon_active",
        "polygon_primary_exchange",
        "polygon_payload_sha256",
        "entry_delta_pct",
        "exit_delta_pct",
        "return_delta",
        "sensitivity_class",
        "raw_response_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def _sha256_json(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
