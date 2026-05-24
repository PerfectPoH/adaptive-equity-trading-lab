from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_active_only_exploratory_policy_gate as gate
from src.experiments.polygon_active_only_exploratory_policy_gate_validator import (
    validate_polygon_active_only_exploratory_policy_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_active_only_exploratory_policy_gate_20260524")


def test_active_only_exploratory_policy_gate_passes_real_spec() -> None:
    report = validate_polygon_active_only_exploratory_policy_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_ACTIVE_ONLY_EXPLORATORY_POLICY_GATE_PASS"


def test_active_only_exploratory_policy_gate_fails_if_promotion_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["promotion_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_active_only_exploratory_policy_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_evaluate_active_only_policy_allows_exploration_but_blocks_promotion() -> None:
    active = {"decision": "POLYGON_ACTIVE_UNIVERSE_SEED_PASS", "active_common_stock_seed_count": 524}
    liquidity = {"decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS", "liquid_candidate_count": 359, "matched_seed_bar_count": 515}
    delisted = {"decision": "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED", "list_date_present_count": 0}

    decision = gate.evaluate_active_only_exploratory_policy(active, liquidity, delisted)

    assert decision["decision"] == "POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_ALLOWED_NO_PROMOTION"
    assert decision["active_only_exploratory_research_allowed"] is True
    assert decision["survivorship_free_claim_allowed"] is False
    assert decision["strategy_promotion_allowed"] is False
    assert decision["broad_survivorship_free_backtest_allowed"] is False
    assert "active_only_survivorship_bias_declared" in decision["mandatory_caveats"]


def test_run_active_only_policy_gate_writes_no_query_artifacts(tmp_path: Path) -> None:
    decision = gate.run_polygon_active_only_exploratory_policy_gate(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = gate.validate_polygon_active_only_exploratory_policy_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
