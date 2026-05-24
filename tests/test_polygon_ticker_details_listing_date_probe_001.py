from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_ticker_details_listing_date_probe_001 as probe
from src.experiments.polygon_ticker_details_listing_date_probe_validator import (
    validate_polygon_ticker_details_listing_date_probe_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_ticker_details_listing_date_probe_20260524")


def test_polygon_ticker_details_listing_date_gate_passes_real_spec() -> None:
    report = validate_polygon_ticker_details_listing_date_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_TICKER_DETAILS_LISTING_DATE_PROBE_GATE_PASS"


def test_polygon_ticker_details_listing_date_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_ticker_details_listing_date_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_ticker_details_payload_passes_when_list_date_present() -> None:
    payload = {
        "results": {
            "ticker": "AAPL",
            "primary_exchange": "XNAS",
            "type": "CS",
            "active": True,
            "list_date": "1980-12-12",
            "cik": "0000320193",
        },
        "status": "OK",
    }

    assessment = probe.assess_ticker_details_listing_date_payload(payload)

    assert assessment["ticker"] == "AAPL"
    assert assessment["has_listing_date"] is True
    assert assessment["listing_date_support_passed"] is True
    assert assessment["broad_universe_backtest_allowed"] is False


def test_assess_ticker_details_payload_blocks_when_list_date_missing() -> None:
    payload = {"results": {"ticker": "AAPL", "primary_exchange": "XNAS", "type": "CS", "active": True}}

    assessment = probe.assess_ticker_details_listing_date_payload(payload)

    assert assessment["listing_date_support_passed"] is False
    assert "missing_list_date" in assessment["blockers"]


def test_run_ticker_details_listing_date_probe_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(
        probe,
        "_fetch_polygon_ticker_details",
        lambda api_key, ticker: {
            "results": {
                "ticker": ticker,
                "primary_exchange": "XNYS",
                "type": "CS",
                "active": True,
                "list_date": "1999-11-18",
                "cik": "0001090872",
            }
        },
    )

    decision = probe.run_polygon_ticker_details_listing_date_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_ticker_details_listing_date_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_TICKER_DETAILS_LISTING_DATE_SUPPORT_PASS"
    assert decision["provider_query_performed"] is True
    assert decision["backtest_performed"] is False
    assert decision["broad_universe_backtest_allowed"] is False
