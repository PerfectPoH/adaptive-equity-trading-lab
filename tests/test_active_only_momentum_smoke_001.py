from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import src.experiments.active_only_momentum_smoke_001 as smoke
from src.experiments.active_only_momentum_smoke_validator import validate_active_only_momentum_smoke_gate


SPEC_DIR = Path("experiments/provider_aware_research/active_only_momentum_smoke_20260524")


def test_active_only_momentum_smoke_gate_passes_real_spec() -> None:
    report = validate_active_only_momentum_smoke_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "ACTIVE_ONLY_MOMENTUM_SMOKE_GATE_PASS"


def test_active_only_momentum_smoke_gate_fails_if_promotion_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "trial_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["promotion_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_active_only_momentum_smoke_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_compute_monthly_top1_momentum_trades_generates_long_only_trades(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    with prices.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "date", "open", "high", "low", "close", "volume", "provider_dataset"])
        writer.writeheader()
        for day in range(1, 91):
            writer.writerow({"symbol": "AAA", "date": f"2024-01-{day:02d}", "open": 10, "high": 10, "low": 10, "close": 10 + day, "volume": 1000, "provider_dataset": "TEST"})
            writer.writerow({"symbol": "BBB", "date": f"2024-01-{day:02d}", "open": 10, "high": 10, "low": 10, "close": 100 - day / 10, "volume": 1000, "provider_dataset": "TEST"})

    trades = smoke.compute_monthly_top1_momentum_trades(
        prices,
        symbols=["AAA", "BBB"],
        lookback_days=21,
        hold_days=10,
        rebalance_step_days=10,
    )

    assert trades
    assert {trade["side"] for trade in trades} == {"long"}
    assert all(trade["symbol"] == "AAA" for trade in trades)


def test_run_active_only_momentum_smoke_writes_no_query_no_promotion_artifacts(tmp_path: Path) -> None:
    decision = smoke.run_active_only_momentum_smoke_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = smoke.validate_active_only_momentum_smoke_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is True
    assert decision["promotion_allowed"] is False
    assert decision["survivorship_free_claim_allowed"] is False
