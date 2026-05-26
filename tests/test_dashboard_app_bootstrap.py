from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_dashboard_app_bootstraps_repo_root_when_run_from_dashboard_dir() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", "import runpy; runpy.run_path('app.py', run_name='dashboard_bootstrap_test')"],
        cwd=repo_root / "dashboard",
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
