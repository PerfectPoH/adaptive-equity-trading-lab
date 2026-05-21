from __future__ import annotations

import csv
from pathlib import Path

from src.experiments.alpha_candidate_factory import (
    build_alpha_candidates,
    rank_candidates,
    run_alpha_candidate_factory,
    validate_alpha_candidate_factory,
)


def test_alpha_candidate_factory_builds_diverse_candidate_queue() -> None:
    candidates = build_alpha_candidates()
    decisions = {candidate["decision"] for candidate in candidates}

    assert len(candidates) >= 10
    assert "blocked_provider_dependency" in decisions
    assert "best_diagnostic_probe" in decisions
    assert "best_infrastructure_probe" in decisions
    assert all(candidate["primary_failure_mode"] for candidate in candidates)


def test_alpha_candidate_ranking_is_descending_by_priority_score() -> None:
    ranked = rank_candidates(build_alpha_candidates())
    scores = [candidate["priority_score"] for candidate in ranked]

    assert scores == sorted(scores, reverse=True)
    assert ranked[0]["decision"] == "best_diagnostic_probe"


def test_alpha_candidate_factory_real_artifact_passes_validation() -> None:
    decision = run_alpha_candidate_factory()
    report = validate_alpha_candidate_factory()

    assert decision["decision"] == "ALPHA_CANDIDATE_FACTORY_READY_NO_EXECUTION"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"


def test_alpha_candidate_factory_fails_if_candidate_is_marked_executable(tmp_path: Path) -> None:
    run_alpha_candidate_factory()
    target = _copy_factory(tmp_path)
    candidates_path = target / "alpha_candidates.csv"
    rows = _read_rows(candidates_path)
    rows[0]["decision"] = "run_backtest"
    _write_rows(candidates_path, rows)

    report = validate_alpha_candidate_factory(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "no_forbidden_candidate_decisions" and check["status"] == "fail" for check in report["checks"])


def test_alpha_candidate_factory_fails_if_not_ranked(tmp_path: Path) -> None:
    run_alpha_candidate_factory()
    target = _copy_factory(tmp_path)
    candidates_path = target / "alpha_candidates.csv"
    rows = _read_rows(candidates_path)
    rows[0]["priority_score"], rows[-1]["priority_score"] = rows[-1]["priority_score"], rows[0]["priority_score"]
    _write_rows(candidates_path, rows)

    report = validate_alpha_candidate_factory(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "ranked_descending" and check["status"] == "fail" for check in report["checks"])


def _copy_factory(tmp_path: Path) -> Path:
    source = Path("experiments/provider_aware_research/alpha_candidate_factory_20260521")
    target = tmp_path / "factory"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
