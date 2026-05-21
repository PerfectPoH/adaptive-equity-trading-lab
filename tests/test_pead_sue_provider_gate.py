from __future__ import annotations

import json
from pathlib import Path

from src.experiments.pead_sue_provider_gate import build_sue_provider_candidates, run_pead_sue_provider_gate, validate_pead_sue_provider_gate


def test_build_sue_provider_candidates_contains_no_return_proxy() -> None:
    candidates = build_sue_provider_candidates()

    assert len(candidates) >= 3
    assert all("return" not in candidate["required_fields"].lower() for candidate in candidates)
    assert any("Intrinio Zacks" in candidate["provider"] for candidate in candidates)


def test_pead_sue_provider_gate_blocks_without_validated_entitlement() -> None:
    decision = run_pead_sue_provider_gate()
    report = validate_pead_sue_provider_gate()

    assert decision["decision"] == "BLOCKED_PIT_SUE_PROVIDER_UNAVAILABLE"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"


def test_pead_sue_provider_gate_fails_if_candidate_is_marked_available(tmp_path: Path) -> None:
    run_pead_sue_provider_gate()
    source = Path("experiments/provider_aware_research/pead_sue_provider_gate_20260521")
    target = tmp_path / "gate"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    candidate_path = target / "sue_provider_candidates.csv"
    candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8").replace("blocked_no_api_key_detected", "available"),
        encoding="utf-8",
    )

    report = validate_pead_sue_provider_gate(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "all_candidates_blocked" and check["status"] == "fail" for check in report["checks"])
