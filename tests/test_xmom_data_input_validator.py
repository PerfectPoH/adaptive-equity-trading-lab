from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_data_input_validator import main, validate_xmom_data_input


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "databento_xmom"
    data_dir.mkdir()
    prices = data_dir / "prices.csv"
    prices.write_text(
        "\n".join(
            [
                "symbol,date,open,high,low,close,volume",
                "AAA,2024-01-02,10.0,10.5,9.8,10.2,100000",
                "AAA,2024-01-03,10.2,10.8,10.1,10.6,110000",
                "BBB,2024-01-02,20.0,21.0,19.5,20.5,120000",
                "BBB,2024-01-03,20.5,21.2,20.1,20.9,130000",
            ]
        ),
        encoding="utf-8",
    )
    manifest = {
        "dataset_id": "databento_xmom_test",
        "provider": "Databento",
        "provider_dataset": "EQUS.MINI",
        "created_at_utc": "2026-05-20T00:00:00Z",
        "requested_by": "test",
        "api_configuration": {"schema": "ohlcv-1d", "symbols": ["AAA", "BBB"]},
        "timezone": "UTC",
        "price_adjustment_policy": "provider_adjusted_or_declared",
        "raw_payload_retention": False,
        "immutable_after_validation": True,
        "expected_symbols": ["AAA", "BBB"],
        "date_range": {"start": "2024-01-02", "end": "2024-01-03"},
        "sanity_thresholds": {"max_abs_close_to_close_return": 5.0, "max_intraday_range_pct": 5.0},
        "data_files": [{"path": "prices.csv", "sha256": _sha256(prices), "role": "ohlcv"}],
    }
    (data_dir / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return data_dir


def test_xmom_data_input_validator_passes_valid_dataset(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)

    report = validate_xmom_data_input(data_dir)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "DATA_INPUT_VALIDATION_PASS"
    assert report["summary"]["failed"] == 0


def test_xmom_data_input_validator_fails_missing_manifest(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)
    (data_dir / "dataset_manifest.json").unlink()

    report = validate_xmom_data_input(data_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:dataset_manifest.json" and check["status"] == "fail" for check in report["checks"])


def test_xmom_data_input_validator_fails_hash_mismatch(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)
    manifest = json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    manifest["data_files"][0]["sha256"] = "bad"
    (data_dir / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_data_input(data_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "data_file_entry:0" and check["status"] == "fail" for check in report["checks"])


def test_xmom_data_input_validator_fails_duplicate_symbol_date(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)
    prices = data_dir / "prices.csv"
    prices.write_text(prices.read_text(encoding="utf-8") + "\nAAA,2024-01-03,10.2,10.8,10.1,10.6,110000", encoding="utf-8")
    manifest = json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    manifest["data_files"][0]["sha256"] = _sha256(prices)
    (data_dir / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_data_input(data_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "no_duplicate_symbol_date" and check["status"] == "fail" for check in report["checks"])


def test_xmom_data_input_validator_fails_invalid_prices(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)
    prices = data_dir / "prices.csv"
    prices.write_text(
        "symbol,date,open,high,low,close,volume\nAAA,2024-01-02,10.0,10.5,9.8,0.0,100000\nBBB,2024-01-02,20.0,19.0,21.0,20.5,120000\n",
        encoding="utf-8",
    )
    manifest = json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    manifest["data_files"][0]["sha256"] = _sha256(prices)
    manifest["date_range"] = {"start": "2024-01-02", "end": "2024-01-02"}
    (data_dir / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_data_input(data_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "prices_positive" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "ohlc_relationships_valid" and check["status"] == "fail" for check in report["checks"])


def test_xmom_data_input_validator_cli_writes_report(tmp_path: Path) -> None:
    data_dir = _valid_data_dir(tmp_path)

    assert main(["--data-dir", str(data_dir), "--write-report"]) == 0

    report_path = data_dir / "data_input_validation_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
