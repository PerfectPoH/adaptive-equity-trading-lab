from __future__ import annotations

import json
from pathlib import Path

from src.experiments.pead_sue_entitlement_pack import (
    build_one_call_probe_spec,
    build_provider_questions,
    run_pead_sue_entitlement_pack,
    validate_pead_sue_entitlement_pack,
)


def test_provider_questions_cover_pit_revision_and_retention() -> None:
    questions = build_provider_questions()
    topics = {question["topic"] for question in questions}

    assert "point_in_time_availability" in topics
    assert "revision_policy" in topics
    assert "license_and_retention" in topics
    assert all("return" not in question["required_answer"].lower() for question in questions)


def test_one_call_probe_spec_blocks_execution_and_requires_sue_schema() -> None:
    spec = build_one_call_probe_spec()
    fields = set(spec["required_output_fields"])

    assert spec["max_provider_calls"] == 1
    assert spec["raw_payload_retention"] is False
    assert spec["network_call_authorized_now"] is False
    assert spec["backtest_authorized"] is False
    assert {"actual_eps", "consensus_eps_or_estimated_eps", "surprise_magnitude"}.issubset(fields)


def test_pead_sue_entitlement_pack_is_ready_but_not_executable() -> None:
    decision = run_pead_sue_entitlement_pack()
    report = validate_pead_sue_entitlement_pack()

    assert decision["decision"] == "READY_FOR_SUE_PROVIDER_ENTITLEMENT_VERIFICATION"
    assert decision["provider_query_performed_now"] is False
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"


def test_entitlement_pack_fails_if_future_probe_allows_more_than_one_call(tmp_path: Path) -> None:
    run_pead_sue_entitlement_pack()
    source = Path("experiments/provider_aware_research/pead_sue_entitlement_pack_20260521")
    target = tmp_path / "pack"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    spec_path = target / "one_call_probe_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["max_provider_calls"] = 2
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    report = validate_pead_sue_entitlement_pack(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "single_call_limit" and check["status"] == "fail" for check in report["checks"])


def test_entitlement_pack_fails_if_price_reaction_proxy_is_not_blocked(tmp_path: Path) -> None:
    run_pead_sue_entitlement_pack()
    source = Path("experiments/provider_aware_research/pead_sue_entitlement_pack_20260521")
    target = tmp_path / "pack"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    blocked_path = target / "blocked_actions.csv"
    blocked_path.write_text(
        blocked_path.read_text(encoding="utf-8").replace("infer_sue_from_price_reaction,blocked", "infer_sue_from_price_reaction,allowed"),
        encoding="utf-8",
    )

    report = validate_pead_sue_entitlement_pack(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocks_price_reaction_sue" and check["status"] == "fail" for check in report["checks"])
