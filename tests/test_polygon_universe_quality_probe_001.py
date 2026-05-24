from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_universe_quality_probe_001 as probe
from src.experiments.polygon_universe_quality_probe_validator import validate_polygon_universe_quality_probe_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_universe_quality_probe_20260524")


def _row(ticker: str, exchange: str = "XNAS", security_type: str = "CS", active: bool = True) -> dict[str, object]:
    return {
        "ticker": ticker,
        "market": "stocks",
        "locale": "us",
        "primary_exchange": exchange,
        "type": security_type,
        "active": active,
        "delisted_utc": None,
        "cik": "0000000000",
    }


def test_polygon_universe_quality_gate_passes_real_spec() -> None:
    report = validate_polygon_universe_quality_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_UNIVERSE_QUALITY_PROBE_GATE_PASS"


def test_polygon_universe_quality_gate_fails_if_price_download_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["market_data_download_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_universe_quality_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "market_download_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_universe_quality_passes_with_large_common_stock_sample() -> None:
    rows = [_row(f"T{i:04d}") for i in range(320)]
    rows += [_row("ETF1", security_type="ETF"), _row("OTC1", exchange="OTCM")]

    assessment = probe.assess_polygon_universe_quality_payload({"results": rows})

    assert assessment["record_count"] == 322
    assert assessment["candidate_common_stock_count"] == 320
    assert assessment["metadata_coverage"]["ticker"] == 1.0
    assert assessment["passes_reference_universe_quality"] is True
    assert assessment["blockers"] == []


def test_assess_universe_quality_blocks_small_reference_sample() -> None:
    rows = [_row(f"T{i:04d}") for i in range(12)]

    assessment = probe.assess_polygon_universe_quality_payload({"results": rows})

    assert assessment["passes_reference_universe_quality"] is False
    assert "candidate_count_below_300" in assessment["blockers"]


def test_run_polygon_universe_quality_probe_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
    rows = [_row(f"T{i:04d}") for i in range(305)]
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(probe, "_fetch_polygon_active_tickers", lambda api_key, limit: {"results": rows, "status": "OK"})

    decision = probe.run_polygon_universe_quality_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_universe_quality_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_UNIVERSE_REFERENCE_QUALITY_PASS"
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
    assert (tmp_path / "out" / "candidate_reference_universe_sample.csv").is_file()
