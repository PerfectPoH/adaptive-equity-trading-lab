import csv
import json
import shutil
from pathlib import Path

from src.experiments.graphify_integration_validator import (
    build_graphify_dry_run_plan,
    validate_graphify_integration,
)


SPEC_DIR = Path("experiments/tooling/graphify_integration_20260523")


def test_graphify_integration_artifact_passes_without_running_graphify():
    result = validate_graphify_integration(SPEC_DIR)

    assert result.passed
    assert result.artifact_id == "GRAPHIFY-INTEGRATION-001"

    manifest = json.loads((SPEC_DIR / "graphify_integration_manifest.json").read_text())
    assert manifest["execution_performed"] is False
    assert manifest["raw_graph_outputs_retained"] is False


def test_graphify_dry_run_plan_is_local_and_non_executing():
    plan = build_graphify_dry_run_plan(
        SPEC_DIR,
        target_scope="src",
        output_dir="experiments/tooling/graphify_runs/graphify_src_20260523",
    )

    assert plan["status"] == "DRY_RUN_READY"
    assert plan["graphify_execution_performed"] is False
    assert plan["command"] == ["graphify", "src"]
    assert "No market data download is authorized." in plan["notes"]
    assert "experiments/tooling/graphify_runs/graphify_src_20260523/graphify-out/graph.json" in plan[
        "expected_outputs"
    ]


def test_graphify_dry_run_blocks_unapproved_repo_root_scan():
    plan = build_graphify_dry_run_plan(
        SPEC_DIR,
        target_scope=".",
        output_dir="experiments/tooling/graphify_runs/root_scan",
    )

    assert plan["status"] == "BLOCKED"
    assert plan["graphify_execution_performed"] is False
    assert "target scope is not approved: ." in plan["reasons"]


def test_graphify_dry_run_blocks_sensitive_provider_outputs():
    blocked_scope = "experiments/provider_aware_research/execution_outputs"
    plan = build_graphify_dry_run_plan(
        SPEC_DIR,
        target_scope=blocked_scope,
        output_dir="experiments/tooling/graphify_runs/provider_outputs",
    )

    assert plan["status"] == "BLOCKED"
    assert f"target scope is not approved: {blocked_scope}" in plan["reasons"]
    assert f"target scope is explicitly blocked: {blocked_scope}" in plan["reasons"]


def test_graphify_validator_fails_if_secret_path_guardrail_is_removed(tmp_path):
    copied_spec = tmp_path / "graphify_spec"
    shutil.copytree(SPEC_DIR, copied_spec)

    blocked_path_file = copied_spec / "blocked_paths.csv"
    rows = list(csv.DictReader(blocked_path_file.read_text(encoding="utf-8").splitlines()))
    rows = [row for row in rows if row["path"] != ".env"]

    with blocked_path_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "status", "reason"])
        writer.writeheader()
        writer.writerows(rows)

    result = validate_graphify_integration(copied_spec)

    assert not result.passed
    assert "missing required blocked paths: .env" in result.reasons
