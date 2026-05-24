from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.polygon_pit_membership_policy_gate_001 import (
    evaluate_polygon_pit_membership_policy,
    run_polygon_pit_membership_policy_gate_001,
    validate_polygon_pit_membership_policy_output,
)
from src.experiments.polygon_pit_membership_policy_gate_validator import validate_polygon_pit_membership_policy_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_pit_membership_policy_gate_20260524")


def test_polygon_pit_membership_policy_gate_passes_real_spec() -> None:
    report = validate_polygon_pit_membership_policy_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_PIT_MEMBERSHIP_POLICY_GATE_PASS"


def test_polygon_pit_membership_policy_gate_fails_if_broad_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["broad_universe_backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_pit_membership_policy_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "broad_backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_evaluate_policy_blocks_broad_backtest_but_allows_single_day_snapshot() -> None:
    active = {"decision": "POLYGON_ACTIVE_UNIVERSE_SEED_PASS", "active_common_stock_seed_count": 524}
    liquidity = {"decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS", "liquid_candidate_count": 359, "matched_seed_bar_count": 515}
    delisted = {"decision": "POLYGON_DELISTED_METADATA_SUPPORT_PASS", "delisted_common_stock_count": 303}

    decision = evaluate_polygon_pit_membership_policy(active, liquidity, delisted)

    assert decision["decision"] == "POLYGON_DATA_STACK_READY_SINGLE_DAY_ONLY"
    assert decision["single_day_liquid_snapshot_allowed"] is True
    assert decision["broad_universe_backtest_allowed"] is False
    assert "listing_dates_unavailable" in decision["broad_backtest_blockers"]
    assert "asof_membership_history_unconstructed" in decision["broad_backtest_blockers"]


def test_evaluate_policy_blocks_if_liquidity_probe_missing() -> None:
    active = {"decision": "POLYGON_ACTIVE_UNIVERSE_SEED_PASS", "active_common_stock_seed_count": 524}
    liquidity = {"decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_BLOCKED", "liquid_candidate_count": 0}
    delisted = {"decision": "POLYGON_DELISTED_METADATA_SUPPORT_PASS", "delisted_common_stock_count": 303}

    decision = evaluate_polygon_pit_membership_policy(active, liquidity, delisted)

    assert decision["single_day_liquid_snapshot_allowed"] is False
    assert "liquidity_probe_not_passed" in decision["single_day_blockers"]


def test_run_polygon_pit_membership_policy_writes_non_executable_artifacts(tmp_path: Path) -> None:
    active = tmp_path / "active.json"
    liquidity = tmp_path / "liquidity.json"
    delisted = tmp_path / "delisted.json"
    active.write_text(json.dumps({"decision": "POLYGON_ACTIVE_UNIVERSE_SEED_PASS", "active_common_stock_seed_count": 524}), encoding="utf-8")
    liquidity.write_text(json.dumps({"decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS", "liquid_candidate_count": 359, "matched_seed_bar_count": 515}), encoding="utf-8")
    delisted.write_text(json.dumps({"decision": "POLYGON_DELISTED_METADATA_SUPPORT_PASS", "delisted_common_stock_count": 303}), encoding="utf-8")

    decision = run_polygon_pit_membership_policy_gate_001(
        spec_dir=SPEC_DIR,
        active_decision_path=active,
        liquidity_decision_path=liquidity,
        delisted_decision_path=delisted,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = validate_polygon_pit_membership_policy_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["broad_universe_backtest_allowed"] is False
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
