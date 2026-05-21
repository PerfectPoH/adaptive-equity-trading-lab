from __future__ import annotations

import json
from pathlib import Path

from src.experiments.pead_earnings_only_gate import run_pead_earnings_only_gate, validate_pead_earnings_only_gate


def test_pead_earnings_only_gate_is_closed_and_validated() -> None:
    decision = run_pead_earnings_only_gate()
    report = validate_pead_earnings_only_gate()

    assert decision["decision"] == "BLOCKED_PROVIDER_EARNINGS_CALENDAR_UNAVAILABLE"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"
    assert report["gate_decision"] == "PEAD_EARNINGS_ONLY_GATE_PASS_BLOCKED_CLOSED"


def test_pead_earnings_only_gate_fails_if_daily_gap_trigger_is_allowed(tmp_path: Path) -> None:
    run_pead_earnings_only_gate()
    source = Path("experiments/provider_aware_research/pead_earnings_only_gate_20260521")
    target = tmp_path / "gate"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path = target / "pead_preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["daily_gap_trigger_allowed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_pead_earnings_only_gate(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "daily_gap_trigger_forbidden" and check["status"] == "fail" for check in report["checks"])
