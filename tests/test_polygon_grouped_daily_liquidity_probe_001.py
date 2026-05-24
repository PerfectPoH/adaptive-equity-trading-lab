from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_grouped_daily_liquidity_probe_001 as probe
from src.experiments.polygon_grouped_daily_liquidity_probe_validator import validate_polygon_grouped_daily_liquidity_probe_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_grouped_daily_liquidity_probe_20260524")


def _seed_row(ticker: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "market": "stocks",
        "locale": "us",
        "primary_exchange": "XNAS",
        "type": "CS",
        "active": "True",
        "cik": "0000000000",
        "raw_payload_retained": "False",
    }


def _bar(ticker: str, close: float = 5.0, volume: int = 300_000) -> dict[str, object]:
    return {"T": ticker, "c": close, "v": volume, "o": close, "h": close + 0.2, "l": close - 0.2, "n": 10}


def test_polygon_grouped_daily_liquidity_gate_passes_real_spec() -> None:
    report = validate_polygon_grouped_daily_liquidity_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_GROUPED_DAILY_LIQUIDITY_PROBE_GATE_PASS"


def test_polygon_grouped_daily_liquidity_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_grouped_daily_liquidity_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_grouped_daily_liquidity_passes_with_available_liquid_seed() -> None:
    seed_rows = [_seed_row(f"T{i:04d}") for i in range(320)]
    payload = {"results": [_bar(f"T{i:04d}") for i in range(310)]}

    assessment = probe.assess_grouped_daily_liquidity_payload(payload, seed_rows=seed_rows)

    assert assessment["seed_count"] == 320
    assert assessment["matched_seed_bar_count"] == 310
    assert assessment["liquid_candidate_count"] == 310
    assert assessment["passes_liquidity_probe"] is True
    assert assessment["market_data_downloaded"] is True
    assert assessment["backtest_performed"] is False


def test_assess_grouped_daily_liquidity_blocks_when_too_few_seed_bars_match() -> None:
    seed_rows = [_seed_row(f"T{i:04d}") for i in range(320)]
    payload = {"results": [_bar(f"T{i:04d}") for i in range(20)]}

    assessment = probe.assess_grouped_daily_liquidity_payload(payload, seed_rows=seed_rows)

    assert assessment["passes_liquidity_probe"] is False
    assert "matched_seed_bar_count_below_300" in assessment["blockers"]


def test_run_grouped_daily_liquidity_probe_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
    seed_path = tmp_path / "seed.csv"
    probe._write_csv(seed_path, list(_seed_row("T0000").keys()), [_seed_row(f"T{i:04d}") for i in range(305)])
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(probe, "_fetch_polygon_grouped_daily", lambda api_key, date: {"results": [_bar(f"T{i:04d}") for i in range(305)]})

    decision = probe.run_polygon_grouped_daily_liquidity_probe_001(
        spec_dir=SPEC_DIR,
        seed_path=seed_path,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_grouped_daily_liquidity_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS"
    assert decision["market_data_downloaded"] is True
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
