from __future__ import annotations

from pathlib import Path


DEFAULT_RANKEX_TRIAL_001_METADATA_PATH = Path("data/small_cap_metadata_eligible_subset30_20260511.csv")
DEFAULT_RANKEX_TRIAL_001_VALIDATION_OUTPUT_DIR = Path("experiments/runs/small_cap_rankex_trial_001_validation_2024")
RANKEX_TRIAL_001_VALIDATION_START = "2024-01-02"
RANKEX_TRIAL_001_VALIDATION_END = "2024-12-31"
RANKEX_TRIAL_001_ID = "TRIAL-RANKEX-001"


def build_rankex_trial_001_validation_cli_args(
    *,
    metadata_path: str | Path = DEFAULT_RANKEX_TRIAL_001_METADATA_PATH,
    output_dir: str | Path = DEFAULT_RANKEX_TRIAL_001_VALIDATION_OUTPUT_DIR,
) -> list[str]:
    return [
        "--metadata-path",
        str(metadata_path),
        "--output-dir",
        str(output_dir),
        "--start",
        RANKEX_TRIAL_001_VALIDATION_START,
        "--end",
        RANKEX_TRIAL_001_VALIDATION_END,
        "--trial-id",
        RANKEX_TRIAL_001_ID,
    ]


def build_rankex_trial_001_validation_powershell_command(
    *,
    metadata_path: str | Path = DEFAULT_RANKEX_TRIAL_001_METADATA_PATH,
    output_dir: str | Path = DEFAULT_RANKEX_TRIAL_001_VALIDATION_OUTPUT_DIR,
) -> str:
    args = build_rankex_trial_001_validation_cli_args(metadata_path=metadata_path, output_dir=output_dir)
    return ".\\.venv-lab\\Scripts\\python.exe -m src.experiments.small_cap_experiment_cli " + " ".join(args)
