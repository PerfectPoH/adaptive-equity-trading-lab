from __future__ import annotations

import json
from pathlib import Path

from src.analysis.backtest_report import write_backtest_report_markdown


RUNS_DIR = Path("experiments/runs")
OUTPUT_PATH = Path("experiments/backtest_analysis_latest.md")


def latest_run_dir(runs_dir: Path = RUNS_DIR) -> Path:
    runs = sorted([path for path in runs_dir.glob("*") if path.is_dir()])
    if not runs:
        raise FileNotFoundError(f"No experiment runs found in {runs_dir}")
    return runs[-1]


def main() -> None:
    report = write_backtest_report_markdown(latest_run_dir(), OUTPUT_PATH)
    print(json.dumps({"run_id": report["run_id"], "verdict": report["verdict"], "output_path": str(OUTPUT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
