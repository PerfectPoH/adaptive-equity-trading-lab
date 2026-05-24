from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_active_universe_seed_001 as seed
from src.experiments.polygon_active_universe_seed_validator import validate_polygon_active_universe_seed_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_active_universe_seed_20260524")


def _row(ticker: str, exchange: str = "XNAS", security_type: str = "CS", active: bool = True) -> dict[str, object]:
    return {
        "ticker": ticker,
        "market": "stocks",
        "locale": "us",
        "primary_exchange": exchange,
        "type": security_type,
        "active": active,
        "cik": "0000000000",
    }


def test_polygon_active_universe_seed_gate_passes_real_spec() -> None:
    report = validate_polygon_active_universe_seed_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_ACTIVE_UNIVERSE_SEED_GATE_PASS"


def test_polygon_active_universe_seed_gate_requires_downstream_audits(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "seed_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["requires_survivorship_audit_before_backtest"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_active_universe_seed_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "survivorship_audit_required" and check["status"] == "fail" for check in report["checks"])


def test_assess_active_universe_seed_passes_without_delisted_field_for_active_rows() -> None:
    rows = [_row(f"T{i:04d}") for i in range(340)]
    rows += [_row("ETF1", security_type="ETF"), _row("OTC1", exchange="OTCM"), _row("OLD1", active=False)]

    assessment = seed.assess_polygon_active_universe_seed_payload({"results": rows})

    assert assessment["record_count"] == 343
    assert assessment["active_common_stock_seed_count"] == 340
    assert assessment["metadata_coverage"]["ticker"] == 1.0
    assert assessment["metadata_coverage"]["primary_exchange"] == 1.0
    assert assessment["passes_active_universe_seed"] is True
    assert assessment["requires_survivorship_audit_before_backtest"] is True
    assert assessment["requires_liquidity_probe_before_backtest"] is True


def test_assess_active_universe_seed_blocks_when_seed_too_small() -> None:
    rows = [_row(f"T{i:04d}") for i in range(25)]

    assessment = seed.assess_polygon_active_universe_seed_payload({"results": rows})

    assert assessment["passes_active_universe_seed"] is False
    assert "active_common_stock_seed_count_below_300" in assessment["blockers"]


def test_run_polygon_active_universe_seed_writes_full_derived_seed(tmp_path: Path, monkeypatch) -> None:
    rows = [_row(f"T{i:04d}") for i in range(310)]
    monkeypatch.setattr(seed, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(seed, "_fetch_polygon_active_tickers", lambda api_key, limit: {"results": rows, "status": "OK"})

    decision = seed.run_polygon_active_universe_seed_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = seed.validate_polygon_active_universe_seed_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_ACTIVE_UNIVERSE_SEED_PASS"
    assert decision["backtest_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["promotion_allowed"] is False
    assert decision["requires_survivorship_audit_before_backtest"] is True
    assert decision["requires_liquidity_probe_before_backtest"] is True
