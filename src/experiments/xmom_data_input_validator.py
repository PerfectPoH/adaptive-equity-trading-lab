from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


MANIFEST_NAME = "dataset_manifest.json"
VALIDATION_REPORT_NAME = "data_input_validation_report.json"
REQUIRED_MANIFEST_FIELDS = {
    "dataset_id",
    "provider",
    "provider_dataset",
    "created_at_utc",
    "requested_by",
    "api_configuration",
    "timezone",
    "price_adjustment_policy",
    "raw_payload_retention",
    "immutable_after_validation",
    "expected_symbols",
    "date_range",
    "data_files",
    "sanity_thresholds",
}
REQUIRED_PRICE_COLUMNS = {"symbol", "date", "open", "high", "low", "close", "volume"}


def validate_xmom_data_input(data_dir: str | Path) -> dict[str, Any]:
    data_path = Path(data_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "data_dir_exists", data_path.exists() and data_path.is_dir(), str(data_path))
    if not data_path.exists() or not data_path.is_dir():
        return _report(data_path, checks)

    manifest_path = data_path / MANIFEST_NAME
    _add_check(checks, f"required_file:{MANIFEST_NAME}", manifest_path.exists() and manifest_path.is_file(), str(manifest_path))
    manifest = _read_json(manifest_path, checks, "manifest_json")
    if not isinstance(manifest, dict):
        return _report(data_path, checks)

    _validate_manifest(manifest, data_path, checks)
    frames = _load_data_files(manifest, data_path, checks)
    if frames:
        data = pd.concat(frames, ignore_index=True)
        _validate_price_data(data, manifest, checks)
    else:
        _add_check(checks, "data_files_loaded", False, "no readable data files")

    return _report(data_path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_data_input(args.data_dir)
    if args.write_report:
        output_path = Path(args.data_dir) / VALIDATION_REPORT_NAME
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM provider-aware data input before the pre-run gate can pass.")
    parser.add_argument("--data-dir", required=True, help="Provider-aware XMOM data input directory.")
    parser.add_argument("--write-report", action="store_true", help=f"Write {VALIDATION_REPORT_NAME} inside the data directory.")
    return parser


def _validate_manifest(manifest: dict[str, Any], data_path: Path, checks: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest.keys()))
    expected_symbols = manifest.get("expected_symbols")
    data_files = manifest.get("data_files")
    date_range = manifest.get("date_range")
    thresholds = manifest.get("sanity_thresholds")
    api_configuration = manifest.get("api_configuration")
    immutable_ok = manifest.get("immutable_after_validation") is True
    raw_retention_ok = manifest.get("raw_payload_retention") in {False, "false", "derived_only", "not_retained"}
    expected_symbols_ok = isinstance(expected_symbols, list) and all(str(symbol).strip() for symbol in expected_symbols)
    data_files_ok = isinstance(data_files, list) and bool(data_files)
    date_range_ok = isinstance(date_range, dict) and bool(date_range.get("start")) and bool(date_range.get("end"))
    thresholds_ok = isinstance(thresholds, dict)
    api_config_ok = isinstance(api_configuration, dict) and bool(api_configuration)
    _add_check(
        checks,
        "manifest_required_fields",
        not missing
        and expected_symbols_ok
        and data_files_ok
        and date_range_ok
        and thresholds_ok
        and api_config_ok
        and immutable_ok
        and raw_retention_ok,
        (
            f"missing={missing}; expected_symbols_ok={expected_symbols_ok}; data_files_ok={data_files_ok}; "
            f"date_range_ok={date_range_ok}; thresholds_ok={thresholds_ok}; api_config_ok={api_config_ok}; "
            f"immutable_ok={immutable_ok}; raw_retention_ok={raw_retention_ok}"
        ),
    )
    if isinstance(data_files, list):
        for index, entry in enumerate(data_files):
            _validate_file_entry(index, entry, data_path, checks)


def _validate_file_entry(index: int, entry: Any, data_path: Path, checks: list[dict[str, str]]) -> None:
    if not isinstance(entry, dict):
        _add_check(checks, f"data_file_entry:{index}", False, "entry is not an object")
        return
    relative_path = str(entry.get("path", ""))
    declared_hash = str(entry.get("sha256", ""))
    role = str(entry.get("role", ""))
    path = data_path / relative_path
    path_ok = relative_path and path.exists() and path.is_file()
    hash_ok = path_ok and declared_hash == _sha256_file(path)
    role_ok = role in {"ohlcv", "prices"}
    _add_check(checks, f"data_file_entry:{index}", bool(path_ok and hash_ok and role_ok), f"path={relative_path}; path_ok={path_ok}; hash_ok={hash_ok}; role={role}")


def _load_data_files(manifest: dict[str, Any], data_path: Path, checks: list[dict[str, str]]) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    data_files = manifest.get("data_files")
    if not isinstance(data_files, list):
        return frames
    for index, entry in enumerate(data_files):
        if not isinstance(entry, dict):
            continue
        relative_path = str(entry.get("path", ""))
        path = data_path / relative_path
        if not path.exists() or not path.is_file():
            continue
        try:
            frame = pd.read_csv(path)
        except Exception as exc:
            _add_check(checks, f"csv_readable:{relative_path}", False, f"{path}: {exc}")
            continue
        frame["_source_file"] = relative_path
        frames.append(frame)
        _add_check(checks, f"csv_readable:{relative_path}", not frame.empty, f"rows={len(frame)}; columns={len(frame.columns)}")
    return frames


def _validate_price_data(data: pd.DataFrame, manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing_columns = sorted(REQUIRED_PRICE_COLUMNS - set(data.columns))
    _add_check(checks, "price_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return

    normalized = data.copy()
    normalized["symbol"] = normalized["symbol"].astype(str).str.strip()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    for column in ("open", "high", "low", "close", "volume"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    expected_symbols = {str(symbol).strip() for symbol in manifest.get("expected_symbols", [])}
    observed_symbols = set(normalized["symbol"].dropna().astype(str))
    date_range = manifest.get("date_range", {})
    start = pd.to_datetime(date_range.get("start"), errors="coerce")
    end = pd.to_datetime(date_range.get("end"), errors="coerce")
    thresholds = manifest.get("sanity_thresholds", {})
    max_abs_close_return = float(thresholds.get("max_abs_close_to_close_return", 5.0))
    max_intraday_range_pct = float(thresholds.get("max_intraday_range_pct", 5.0))

    finite_price_rows = normalized[["open", "high", "low", "close"]].map(_is_finite_number).all(axis=1)
    positive_prices = (normalized[["open", "high", "low", "close"]] > 0).all(axis=1)
    non_negative_volume = normalized["volume"].map(_is_finite_number) & (normalized["volume"] >= 0)
    high_consistent = normalized["high"] >= normalized[["open", "low", "close"]].max(axis=1)
    low_consistent = normalized["low"] <= normalized[["open", "high", "close"]].min(axis=1)
    duplicate_count = int(normalized.duplicated(["symbol", "date"]).sum())
    dates_parse_ok = normalized["date"].notna().all()
    within_range = normalized["date"].between(start, end, inclusive="both").all() if pd.notna(start) and pd.notna(end) else False
    missing_expected_symbols = sorted(expected_symbols - observed_symbols)
    unexpected_symbols = sorted(observed_symbols - expected_symbols)
    intraday_range_pct = (normalized["high"] - normalized["low"]) / normalized["close"]
    grouped_returns = normalized.sort_values(["symbol", "date"]).groupby("symbol")["close"].pct_change().abs()

    _add_check(checks, "symbols_match_manifest", not missing_expected_symbols and not unexpected_symbols, f"missing={missing_expected_symbols}; unexpected={unexpected_symbols}")
    _add_check(checks, "dates_parse_and_within_range", bool(dates_parse_ok and within_range), f"dates_parse_ok={bool(dates_parse_ok)}; within_range={bool(within_range)}")
    _add_check(checks, "no_duplicate_symbol_date", duplicate_count == 0, f"duplicate_count={duplicate_count}")
    _add_check(checks, "prices_finite", bool(finite_price_rows.all()), f"bad_rows={int((~finite_price_rows).sum())}")
    _add_check(checks, "prices_positive", bool(positive_prices.all()), f"bad_rows={int((~positive_prices).sum())}")
    _add_check(checks, "volume_non_negative", bool(non_negative_volume.all()), f"bad_rows={int((~non_negative_volume).sum())}")
    _add_check(checks, "ohlc_relationships_valid", bool((high_consistent & low_consistent).all()), f"bad_rows={int((~(high_consistent & low_consistent)).sum())}")
    _add_check(
        checks,
        "intraday_range_within_sanity_threshold",
        bool((intraday_range_pct <= max_intraday_range_pct).all()),
        f"max_intraday_range_pct={float(intraday_range_pct.max())}; threshold={max_intraday_range_pct}",
    )
    return_ok = grouped_returns.dropna().le(max_abs_close_return).all()
    max_return = grouped_returns.dropna().max()
    _add_check(
        checks,
        "close_to_close_return_within_sanity_threshold",
        bool(return_ok),
        f"max_abs_return={0.0 if pd.isna(max_return) else float(max_return)}; threshold={max_abs_close_return}",
    )


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(data_path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "data_dir": str(data_path),
        "status": "pass" if not failed else "fail",
        "gate_decision": "DATA_INPUT_VALIDATION_PASS" if not failed else "DATA_INPUT_VALIDATION_FAIL",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
