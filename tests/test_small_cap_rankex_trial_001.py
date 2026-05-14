from __future__ import annotations

from src.experiments.small_cap_rankex_trial_001 import (
    DEFAULT_RANKEX_TRIAL_001_METADATA_PATH,
    DEFAULT_RANKEX_TRIAL_001_VALIDATION_OUTPUT_DIR,
    build_rankex_trial_001_validation_cli_args,
    build_rankex_trial_001_validation_powershell_command,
)


def test_build_rankex_trial_001_validation_cli_args_matches_preregistration() -> None:
    args = build_rankex_trial_001_validation_cli_args()

    assert args == [
        "--metadata-path",
        str(DEFAULT_RANKEX_TRIAL_001_METADATA_PATH),
        "--output-dir",
        str(DEFAULT_RANKEX_TRIAL_001_VALIDATION_OUTPUT_DIR),
        "--start",
        "2024-01-02",
        "--end",
        "2024-12-31",
        "--trial-id",
        "TRIAL-RANKEX-001",
    ]


def test_build_rankex_trial_001_validation_cli_args_allows_explicit_paths() -> None:
    args = build_rankex_trial_001_validation_cli_args(
        metadata_path="data/custom_metadata.csv",
        output_dir="experiments/runs/custom_rankex_validation",
    )

    assert args[:4] == [
        "--metadata-path",
        "data/custom_metadata.csv",
        "--output-dir",
        "experiments/runs/custom_rankex_validation",
    ]
    assert args[-2:] == ["--trial-id", "TRIAL-RANKEX-001"]


def test_build_rankex_trial_001_validation_powershell_command_is_non_executing() -> None:
    command = build_rankex_trial_001_validation_powershell_command()

    assert command.startswith(r".\.venv-lab\Scripts\python.exe -m src.experiments.small_cap_experiment_cli")
    assert "--trial-id TRIAL-RANKEX-001" in command
    assert "--start 2024-01-02" in command
    assert "--end 2024-12-31" in command
