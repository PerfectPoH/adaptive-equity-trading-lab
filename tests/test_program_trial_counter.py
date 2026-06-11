from __future__ import annotations

from pathlib import Path

from src.validation.program_trial_counter import count_runs, program_trial_count, program_wide_trial_count


def test_counts_families_from_run_directories(tmp_path: Path) -> None:
    runs = tmp_path / "experiments" / "runs"
    for name in ["studio_oos_001_x", "studio_oos_002_y", "true_etf_001_z", "unrelated_run"]:
        (runs / name).mkdir(parents=True)
    counts = count_runs(root=tmp_path)
    assert counts["studio_oos"] == 2
    assert counts["true_etf"] == 1
    assert counts["total"] == 4


def test_program_trial_count_is_runs_plus_one_with_floor(tmp_path: Path) -> None:
    runs = tmp_path / "experiments" / "runs"
    (runs / "true_etf_001_z").mkdir(parents=True)
    assert program_trial_count("true_etf", root=tmp_path) == 2
    (runs / "true_etf_002_w").mkdir(parents=True)
    (runs / "true_etf_003_v").mkdir(parents=True)
    assert program_trial_count("true_etf", root=tmp_path) == 4
    assert program_wide_trial_count(root=tmp_path) == 3
