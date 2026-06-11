from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import inspect


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
    from dashboard.app import COLOR_LOGIC, color_logic_component_html

    assert set(COLOR_LOGIC) == {"Blue", "Mint", "Amber", "Plum", "Rose"}
    assert len({item["body"] for item in COLOR_LOGIC.values()}) == 5
    assert COLOR_LOGIC["Rose"]["body"] != COLOR_LOGIC["Blue"]["body"]
    html = color_logic_component_html()
    assert "addEventListener(\"click\"" in html
    assert "selectColor(\"Blue\")" in html
    assert "aria-pressed" in html


def test_dashboard_app_exposes_mission_control_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard.app import SECTIONS

    assert "Mission Brief" in SECTIONS
    assert "Strategy Builder" in SECTIONS
    assert "Data Vault" in SECTIONS
    assert "Command Center" not in SECTIONS


def test_mission_control_routes_do_not_clone_full_data_dashboard() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard import app

    focused_routes = [
        app.render_regime_playbook,
        app.render_data_vault,
        app.render_decision_ledger,
    ]

    for route in focused_routes:
        source = inspect.getsource(route)
        assert "render_results_and_data" not in source


def test_dashboard_main_uses_internal_rail_not_streamlit_sidebar() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard import app

    source = inspect.getsource(app.main)

    assert "mission_rail_navigation" in source
    # Rail is always visible after the redesign: no collapsed toggle in main(),
    # only the state key that keeps it pinned open.
    assert "mission_rail_open" in source
    assert "sidebar_navigation" not in source
    assert "main_navigation" not in source
    assert "shell_nav" not in source


def test_mission_rail_navigation_is_not_streamlit_sidebar_bound() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard import app

    source = inspect.getsource(app.mission_rail_navigation)

    assert "st.sidebar" not in source
    assert "st.button" in source


def test_collapsed_mission_rail_uses_separate_toggle_state_key() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard import app

    source = inspect.getsource(app.collapsed_mission_rail_toggle)

    assert "mission_rail_open_button" in source
    assert 'key="mission_rail_open"' not in source
    assert "set_mission_rail_open" in source
