from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_ticker_reference_probe_001 as probe
from src.experiments.polygon_ticker_reference_probe_validator import validate_polygon_ticker_reference_probe_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_ticker_reference_probe_20260524")


def test_polygon_ticker_reference_probe_gate_passes_real_spec() -> None:
    report = validate_polygon_ticker_reference_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_TICKER_REFERENCE_PROBE_GATE_PASS"


def test_polygon_ticker_reference_probe_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_ticker_reference_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_polygon_payload_passes_when_required_fields_exist() -> None:
    payload = {
        "results": [
            {
                "ticker": "AAPL",
                "market": "stocks",
                "locale": "us",
                "primary_exchange": "XNAS",
                "type": "CS",
                "active": True,
                "currency_name": "usd",
                "cik": "0000320193",
                "composite_figi": "BBG000B9XRY4",
                "share_class_figi": "BBG001S5N8V8",
                "delisted_utc": None,
            }
        ],
        "status": "OK",
    }

    assessment = probe.assess_polygon_ticker_payload(payload)

    assert assessment["record_count"] == 1
    assert assessment["has_ticker"] is True
    assert assessment["has_exchange"] is True
    assert assessment["has_security_type"] is True
    assert assessment["has_active_status"] is True
    assert assessment["has_delisted_metadata"] is True
    assert assessment["passes_universe_gate_requirements"] is True
    assert assessment["blockers"] == []


def test_assess_polygon_payload_blocks_when_delisted_metadata_missing() -> None:
    payload = {
        "results": [
            {
                "ticker": "AAPL",
                "primary_exchange": "XNAS",
                "type": "CS",
                "active": True,
            }
        ]
    }

    assessment = probe.assess_polygon_ticker_payload(payload)

    assert assessment["passes_universe_gate_requirements"] is False
    assert "missing_delisted_metadata" in assessment["blockers"]


def test_run_polygon_probe_writes_clean_artifacts_with_monkeypatched_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(
        probe,
        "_fetch_polygon_tickers",
        lambda api_key, limit: {
            "results": [
                {
                    "ticker": "AAPL",
                    "primary_exchange": "XNAS",
                    "type": "CS",
                    "active": True,
                    "delisted_utc": None,
                }
            ],
            "status": "OK",
        },
    )

    decision = probe.run_polygon_ticker_reference_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_ticker_reference_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_TICKER_REFERENCE_SOURCE_PASS"
    assert decision["provider_query_performed"] is True
    assert decision["raw_payload_retained"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
    assert (tmp_path / "out" / "derived_ticker_sample.csv").is_file()
