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


def test_workbench_color_logic_has_distinct_meanings() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard.app import COLOR_LOGIC

    assert set(COLOR_LOGIC) == {"Blue", "Mint", "Amber", "Plum", "Rose"}
    assert len({item["body"] for item in COLOR_LOGIC.values()}) == 5
    assert COLOR_LOGIC["Rose"]["body"] != COLOR_LOGIC["Blue"]["body"]
