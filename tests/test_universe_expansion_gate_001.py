from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from src.experiments.universe_expansion_gate_001 import run_universe_expansion_gate_001, validate_universe_expansion_gate_output
from src.experiments.universe_expansion_gate_validator import validate_universe_expansion_gate


SPEC_DIR = Path("experiments/provider_aware_research/universe_expansion_gate_20260524")


def test_universe_expansion_gate_passes_real_spec() -> None:
    report = validate_universe_expansion_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "UNIVERSE_EXPANSION_GATE_PASS"


def test_universe_expansion_gate_fails_if_backtest_is_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "universe_expansion_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_universe_expansion_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_universe_expansion_gate_requires_quality_rules_and_provider_contract(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    (spec / "provider_requirements.csv").unlink()

    report = validate_universe_expansion_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:provider_requirements.csv" and check["status"] == "fail" for check in report["checks"])


def test_candidate_template_contains_required_columns() -> None:
    with (SPEC_DIR / "candidate_universe_template.csv").open("r", encoding="utf-8", newline="") as handle:
        columns = set(csv.DictReader(handle).fieldnames or [])

    assert {
        "symbol",
        "exchange",
        "security_type",
        "first_trade_date",
        "last_trade_date",
        "median_dollar_volume_60d",
        "median_close_60d",
        "survivorship_source",
        "include_candidate",
        "exclusion_reason",
    }.issubset(columns)


def test_run_universe_expansion_gate_writes_non_executable_artifacts(tmp_path: Path) -> None:
    decision = run_universe_expansion_gate_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = validate_universe_expansion_gate_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "UNIVERSE_EXPANSION_GATE_READY_NOT_EXECUTABLE"
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
