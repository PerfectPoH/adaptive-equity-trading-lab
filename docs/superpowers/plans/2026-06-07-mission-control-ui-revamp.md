# Mission Control UI Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current dense Streamlit dashboard into the approved Mission Control v2 research operating system.

**Architecture:** Add a small testable `dashboard/mission_control_ui.py` layer for navigation metadata, status view models, and reusable HTML fragments. Keep existing quant/data functions unchanged; `dashboard/app.py` becomes a clearer page router that renders Mission Brief, Project Story, Strategy Builder, Portfolio Lab, Regime Playbook, Data Vault, and Decision Ledger.

**Tech Stack:** Python, Streamlit, Plotly, pandas, existing dashboard data helpers, pytest, Browser smoke verification.

---

## File Structure

- Create `dashboard/mission_control_ui.py`: pure/testable UI metadata and HTML builders for the Mission Control shell.
- Modify `dashboard/app.py`: import the new UI helpers, replace the old six-section navigation with Mission Control sections, add new page wrappers, and keep existing render functions reusable.
- Create `tests/test_mission_control_ui.py`: unit tests for the new navigation, status view model, and HTML fragments.
- Modify `tests/test_dashboard_app_bootstrap.py`: assert the app exposes Mission Control labels without breaking bootstrap.
- Add `vault/02-Devlog/2026-06/2026-06-07-mission-control-ui-implementation.md`: implementation audit note.

Do not modify quant research artifacts under `experiments/provider_aware_research/execution_outputs/` during this UI work.

---

### Task 1: Add Mission Control UI Metadata

**Files:**
- Create: `dashboard/mission_control_ui.py`
- Create: `tests/test_mission_control_ui.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mission_control_ui.py`:

```python
from dashboard.mission_control_ui import (
    MISSION_SECTIONS,
    build_mission_status,
    mission_section_by_label,
    mission_sidebar_html,
)


def test_mission_sections_are_beginner_readable() -> None:
    labels = [section.label for section in MISSION_SECTIONS]

    assert labels == [
        "Mission Brief",
        "Project Story",
        "Strategy Builder",
        "Portfolio Lab",
        "Regime Playbook",
        "Data Vault",
        "Decision Ledger",
    ]
    assert all(section.description for section in MISSION_SECTIONS)
    assert all(section.group in {"Start here", "Build", "Audit"} for section in MISSION_SECTIONS)


def test_mission_section_lookup_falls_back_to_brief() -> None:
    assert mission_section_by_label("Portfolio Lab").label == "Portfolio Lab"
    assert mission_section_by_label("Unknown").label == "Mission Brief"


def test_build_mission_status_translates_payload_to_plain_language() -> None:
    payload = {
        "metrics": {
            "promoted_strategy_count": 0,
            "final_policy": "RISK_REGIME_ENGINE_ONLY",
        },
        "current_market_regime": {
            "regime_label": "RANGE_NORMAL",
        },
        "data_readiness": {
            "status": "BLOCKED_TRUE_DATA_MISSING",
        },
    }

    status = build_mission_status(payload)

    assert status["mode"] == "RISK_REGIME_ENGINE_ONLY"
    assert status["promoted"] == 0
    assert status["current_blocker"] == "DATA"
    assert "PIT" in status["plain_english_blocker"]
    assert status["next_gate"] == "Attach admissible data bundle"


def test_mission_sidebar_html_contains_status_and_sections() -> None:
    html = mission_sidebar_html(
        active_label="Portfolio Lab",
        status={
            "mode": "RISK_REGIME_ENGINE_ONLY",
            "promoted": 0,
            "current_blocker": "DATA",
            "next_gate": "Attach admissible data bundle",
            "plain_english_blocker": "Missing PIT and delisted coverage.",
        },
    )

    assert "Adaptive Lab" in html
    assert "Portfolio Lab" in html
    assert "Mission Brief" in html
    assert "active" in html
    assert "Attach admissible data bundle" in html
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_mission_control_ui.py -q
```

Expected: fails with `ModuleNotFoundError` or missing names from `dashboard.mission_control_ui`.

- [ ] **Step 3: Implement the metadata module**

Create `dashboard/mission_control_ui.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any


@dataclass(frozen=True)
class MissionSection:
    label: str
    group: str
    description: str
    legacy_target: str


MISSION_SECTIONS: tuple[MissionSection, ...] = (
    MissionSection("Mission Brief", "Start here", "What the lab is doing now.", "Command Center"),
    MissionSection("Project Story", "Start here", "Why the fortress exists.", "Project Anatomy"),
    MissionSection("Strategy Builder", "Build", "Create one governed idea.", "Strategy Workbench"),
    MissionSection("Portfolio Lab", "Build", "Combine strategy sleeves.", "Portfolio Lab"),
    MissionSection("Regime Playbook", "Build", "Which sleeve works when.", "Results & Data"),
    MissionSection("Data Vault", "Audit", "Providers, blockers, PIT, and delisted coverage.", "Results & Data"),
    MissionSection("Decision Ledger", "Audit", "Every yes/no decision and raw artifact trail.", "Results & Data"),
)


def mission_section_by_label(label: str) -> MissionSection:
    for section in MISSION_SECTIONS:
        if section.label == label:
            return section
    return MISSION_SECTIONS[0]


def build_mission_status(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics", {}), dict) else {}
    readiness = payload.get("data_readiness", {}) if isinstance(payload.get("data_readiness", {}), dict) else {}
    current_regime = payload.get("current_market_regime", {}) if isinstance(payload.get("current_market_regime", {}), dict) else {}
    readiness_status = str(readiness.get("status", "UNKNOWN"))
    blocker = "DATA" if "DATA" in readiness_status or "MISSING" in readiness_status or "BLOCK" in readiness_status else "GOVERNANCE"
    return {
        "mode": str(metrics.get("final_policy", "RISK_REGIME_ENGINE_ONLY")),
        "promoted": int(metrics.get("promoted_strategy_count", 0) or 0),
        "current_blocker": blocker,
        "current_regime": str(current_regime.get("regime_label", "UNKNOWN")),
        "next_gate": "Attach admissible data bundle" if blocker == "DATA" else "Review final decision gate",
        "plain_english_blocker": "Missing PIT and delisted coverage keeps true claims locked."
        if blocker == "DATA"
        else "Governance has not allowed promotion, paper trading, or live trading.",
    }


def mission_sidebar_html(active_label: str, status: dict[str, Any]) -> str:
    grouped: dict[str, list[MissionSection]] = {}
    for section in MISSION_SECTIONS:
        grouped.setdefault(section.group, []).append(section)

    groups_html = []
    for group, sections in grouped.items():
        items = []
        for section in sections:
            active = " active" if section.label == active_label else ""
            items.append(
                f'<div class="mc-nav-item{active}">'
                f'<strong>{escape(section.label)}</strong>'
                f'<span>{escape(section.description)}</span>'
                "</div>"
            )
        groups_html.append(
            f'<div class="mc-nav-group"><div class="mc-nav-label">{escape(group)}</div>'
            + "".join(items)
            + "</div>"
        )

    return (
        '<div class="mc-sidebar-shell">'
        '<div class="mc-brand">Adaptive Lab<span>Research operating system</span></div>'
        + "".join(groups_html)
        + '<div class="mc-status-card">'
        '<span>Current mode</span>'
        f'<strong>{escape(str(status.get("mode", "UNKNOWN")))}</strong>'
        f'<em>{escape(str(status.get("plain_english_blocker", "")))}</em>'
        f'<small>Next: {escape(str(status.get("next_gate", "Review gate")))}</small>'
        "</div></div>"
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_mission_control_ui.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add dashboard/mission_control_ui.py tests/test_mission_control_ui.py
git commit -m "Add Mission Control UI metadata"
```

---

### Task 2: Add Mission Control Theme And Sidebar Shell

**Files:**
- Modify: `dashboard/app.py`
- Modify: `tests/test_dashboard_app_bootstrap.py`

- [ ] **Step 1: Write bootstrap assertions for new labels**

Modify `tests/test_dashboard_app_bootstrap.py` by adding:

```python
def test_dashboard_app_exposes_mission_control_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from dashboard.app import SECTIONS

    assert "Mission Brief" in SECTIONS
    assert "Strategy Builder" in SECTIONS
    assert "Data Vault" in SECTIONS
    assert "Command Center" not in SECTIONS
```

- [ ] **Step 2: Run the assertion and verify it fails**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_dashboard_app_bootstrap.py::test_dashboard_app_exposes_mission_control_sections -q
```

Expected: fails because `SECTIONS` still uses the old labels.

- [ ] **Step 3: Update imports and section labels**

In `dashboard/app.py`, add:

```python
from dashboard.mission_control_ui import (
    MISSION_SECTIONS,
    build_mission_status,
    mission_section_by_label,
    mission_sidebar_html,
)
```

Replace:

```python
SECTIONS = ["Command Center", "Strategies", "Results & Data", "Project Anatomy", "Strategy Workbench", "Portfolio Lab"]
```

with:

```python
SECTIONS = [section.label for section in MISSION_SECTIONS]
```

- [ ] **Step 4: Add Mission Control CSS to `inject_theme`**

Inside the existing `<style>` block in `inject_theme`, add:

```css
.mc-sidebar-shell {
  display: grid;
  gap: 16px;
  padding: 4px 0 18px;
}
.mc-brand {
  color: #0f172a;
  font-size: 18px;
  font-weight: 900;
  line-height: 1.1;
}
.mc-brand span {
  display: block;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  margin-top: 5px;
}
.mc-nav-group {
  display: grid;
  gap: 8px;
}
.mc-nav-label {
  color: #64748b;
  font-family: "IBM Plex Mono", monospace;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin-top: 6px;
}
.mc-nav-item {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 11px;
  background: transparent;
}
.mc-nav-item.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}
.mc-nav-item strong {
  display: block;
  color: #0f172a;
  font-size: 14px;
}
.mc-nav-item.active strong {
  color: #1d4ed8;
}
.mc-nav-item span {
  display: block;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
  margin-top: 3px;
}
.mc-status-card {
  border-radius: 16px;
  background: #0f172a;
  color: #ffffff;
  padding: 14px;
}
.mc-status-card span,
.mc-status-card small,
.mc-status-card em {
  display: block;
  color: #cbd5e1;
  font-size: 12px;
  line-height: 1.4;
  font-style: normal;
}
.mc-status-card strong {
  display: block;
  color: #ffffff;
  font-size: 21px;
  line-height: 1.05;
  margin: 6px 0;
  overflow-wrap: anywhere;
}
.mission-brief-hero {
  border: 1px solid #1e293b;
  border-radius: 24px;
  padding: 36px;
  color: #ffffff;
  background: linear-gradient(135deg, rgba(37,99,235,.96), rgba(15,23,42,.98) 58%, rgba(217,119,6,.78));
  box-shadow: 0 24px 70px rgba(15,23,42,.15);
}
.mission-brief-hero h1 {
  color: #ffffff;
  font-size: clamp(42px, 5vw, 68px);
  line-height: .95;
  letter-spacing: -.04em;
  margin: 10px 0 14px;
}
.mission-brief-hero p {
  color: #dbeafe !important;
  font-size: 17px;
  line-height: 1.58;
  max-width: 880px;
}
```

- [ ] **Step 5: Replace sidebar body**

In `sidebar_navigation`, compute the status and render the new shell before the radio:

```python
status = build_mission_status(payload)
st.markdown(mission_sidebar_html(current_section, status), unsafe_allow_html=True)
```

Keep the `st.radio` for actual Streamlit state selection, but set `label_visibility="collapsed"` so the visual shell explains the structure.

- [ ] **Step 6: Run bootstrap tests**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m pytest tests\test_dashboard_app_bootstrap.py tests\test_mission_control_ui.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 2**

Run:

```powershell
git add dashboard/app.py tests/test_dashboard_app_bootstrap.py
git commit -m "Add Mission Control shell"
```

---

### Task 3: Implement Mission Brief Landing Page

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Add a Mission Brief render function**

Add this function near `render_overview`:

```python
def render_mission_brief(payload: dict[str, object]) -> None:
    metrics = governance_metrics(payload)
    status = build_mission_status({"metrics": metrics, **payload})
    st.markdown(
        f"""
        <div class="mission-brief-hero">
          <div class="lab-kicker">Current mission</div>
          <h1>Build portfolios that know when to stay quiet.</h1>
          <p>
            The lab no longer hunts one magic setup. It tests strategy sleeves, maps market regimes,
            and blocks any claim that cannot survive data quality, costs, robustness, and audit gates.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page_guide(
        "What am I looking at?",
        "A research control room. A block is not a crash; it is the lab refusing to turn weak evidence into a trading claim.",
        [
            ("Create a strategy", "Open Strategy Builder to freeze a single governed hypothesis.", "data"),
            ("Test a portfolio", "Open Portfolio Lab to combine sleeves and inspect dynamic regimes.", "good"),
            ("Inspect blockers", "Open Data Vault to see why true testing is still locked.", "warn"),
            ("Read the story", "Open Project Story to understand how each failure shaped the lab.", "block"),
        ],
    )
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Promoted", metrics["promoted_strategy_count"], "No strategy passed promotion gates")
    with k2:
        metric_card("Mode", status["mode"], "Current operating posture")
    with k3:
        metric_card("Blocker", status["current_blocker"], status["plain_english_blocker"])
    with k4:
        metric_card("Next gate", status["next_gate"], "Required before stronger claims")
    section_note(
        "Use Mission Brief when you want orientation. Use Strategy Builder and Portfolio Lab when you want to work."
    )
```

- [ ] **Step 2: Route `Mission Brief` to the new function**

In `main`, replace the old first branch:

```python
if section == "Command Center":
    render_overview(payload)
```

with:

```python
if section == "Mission Brief":
    render_mission_brief(payload)
```

- [ ] **Step 3: Keep old overview reusable under Decision Ledger if needed**

Do not delete `render_overview`. It can remain as a fallback or be used by `Decision Ledger` in Task 4.

- [ ] **Step 4: Run compile and bootstrap tests**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m py_compile dashboard\app.py dashboard\mission_control_ui.py
.\.venv-lab\Scripts\python.exe -m pytest tests\test_dashboard_app_bootstrap.py tests\test_mission_control_ui.py -q
```

Expected: compile succeeds and tests pass.

- [ ] **Step 5: Browser smoke Mission Brief**

Open `http://localhost:8502/` and verify:

- No traceback.
- Text includes `Build portfolios that know when to stay quiet`.
- Text includes `What am I looking at?`.
- Sidebar includes `Mission Brief`, `Portfolio Lab`, and `Data Vault`.

- [ ] **Step 6: Commit Task 3**

Run:

```powershell
git add dashboard/app.py
git commit -m "Add Mission Brief landing page"
```

---

### Task 4: Split Legacy Pages Into Mission Control Routes

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Add focused wrapper functions**

Add these wrappers near the existing render functions:

```python
def render_project_story(payload: dict[str, object]) -> None:
    page_guide(
        "The life of the project",
        "This page explains why the lab became a fortress: each failed strategy removed one illusion and added one guardrail.",
        [
            ("Ideas", "Momentum, SEC 8-K, PEAD, Form 4, ORB, Kronos, and portfolio sleeves.", "data"),
            ("Failures", "Archived ideas are preserved as evidence, not hidden.", "block"),
            ("Capabilities", "Every failure left infrastructure behind.", "good"),
            ("Next phase", "Dynamic regime portfolios wait for admissible data.", "warn"),
        ],
    )
    render_lab_explainer(payload)


def render_regime_playbook(payload: dict[str, object]) -> None:
    page_guide(
        "Which strategy works when?",
        "The regime playbook explains which strategy families are allowed, reduced, blocked, or observe-only in each market state.",
        [
            ("Regime", "Current market state from the local regime map.", "data"),
            ("Routing", "How each strategy family changes weight by regime.", "good"),
            ("Failure modes", "When a sleeve should stay quiet.", "warn"),
            ("Audit", "Full router matrix remains inspectable.", "block"),
        ],
    )
    render_results_and_data(payload)


def render_data_vault(payload: dict[str, object]) -> None:
    page_guide(
        "Why data is the current blocker",
        "This page focuses on provider readiness, PIT coverage, delisted symbols, and true-backtest admissibility.",
        [
            ("Required fields", "What a real test must have before execution.", "data"),
            ("Provider map", "Norgate, EODHD, FMP, Databento, and remaining gaps.", "good"),
            ("Blocked claims", "No proxy P&L can become promotion.", "block"),
            ("Next gate", "Attach a complete admissible bundle.", "warn"),
        ],
    )
    render_results_and_data(payload)


def render_decision_ledger(payload: dict[str, object]) -> None:
    page_guide(
        "Every decision remains auditable",
        "This page is intentionally raw-heavy. It is where final decisions, provider logs, and artifact paths are inspected.",
        [
            ("Final decisions", "The ledger of archive/block/diagnostic states.", "data"),
            ("Provider rows", "Which runs touched external sources.", "warn"),
            ("Promotion lock", "No hidden green-light path.", "block"),
            ("Artifacts", "Raw tables stay available for review.", "good"),
        ],
    )
    render_results_and_data(payload)
```

- [ ] **Step 2: Update the main router**

Replace the old router block with:

```python
if section == "Mission Brief":
    render_mission_brief(payload)
elif section == "Project Story":
    render_project_story(payload)
elif section == "Strategy Builder":
    render_strategy_workbench()
elif section == "Portfolio Lab":
    render_portfolio_lab(payload)
elif section == "Regime Playbook":
    render_regime_playbook(payload)
elif section == "Data Vault":
    render_data_vault(payload)
elif section == "Decision Ledger":
    render_decision_ledger(payload)
else:
    render_mission_brief(payload)
```

- [ ] **Step 3: Run compile**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m py_compile dashboard\app.py
```

Expected: no output and exit code 0.

- [ ] **Step 4: Browser smoke each route**

Use the browser to click each section:

- Mission Brief
- Project Story
- Strategy Builder
- Portfolio Lab
- Regime Playbook
- Data Vault
- Decision Ledger

Expected on each:

- No traceback.
- Page heading or guide text is visible.
- Sidebar remains usable.

- [ ] **Step 5: Commit Task 4**

Run:

```powershell
git add dashboard/app.py
git commit -m "Route dashboard through Mission Control pages"
```

---

### Task 5: Move Dense Audit Content Behind Consistent Expanders

**Files:**
- Modify: `dashboard/app.py`

- [ ] **Step 1: Search remaining raw-first tables**

Run:

```powershell
rg -n "st\\.dataframe|st\\.json|st\\.code" dashboard/app.py
```

Expected: list of raw output calls.

- [ ] **Step 2: Wrap raw-heavy blocks with explicit labels**

For any raw table shown before a plain-language explanation, wrap it in one of these patterns:

```python
with st.expander("Audit details: raw ledger rows"):
    st.dataframe(ledger, width="stretch", hide_index=True)
```

or:

```python
with st.expander("Audit details: manifest and final decision"):
    st.json(preview["portfolio_manifest"])
    st.json(preview["final_decision"])
```

Do not hide primary metrics, key charts, or user action buttons.

- [ ] **Step 3: Keep explanatory captions before charts**

Before each main chart in Mission Brief, Portfolio Lab, Regime Playbook, and Data Vault, ensure there is either `section_note(...)`, `st.caption(...)`, or a `page_guide(...)` explaining how to read it.

- [ ] **Step 4: Run compile and bootstrap tests**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m py_compile dashboard\app.py
.\.venv-lab\Scripts\python.exe -m pytest tests\test_dashboard_app_bootstrap.py tests\test_mission_control_ui.py -q
```

Expected: compile succeeds and tests pass.

- [ ] **Step 5: Browser visual pass**

Check `http://localhost:8502/` at normal desktop width:

- Main page does not start with a raw dataframe.
- Strategy Builder shows the wizard before audit rows.
- Portfolio Lab shows setup/verdict/dynamic explanation before raw allocation tables.
- Data Vault and Decision Ledger clearly label raw content as audit details.

- [ ] **Step 6: Commit Task 5**

Run:

```powershell
git add dashboard/app.py
git commit -m "Collapse raw audit content behind Mission Control explainers"
```

---

### Task 6: Add Devlog And Final Verification

**Files:**
- Create: `vault/02-Devlog/2026-06/2026-06-07-mission-control-ui-revamp.md`

- [ ] **Step 1: Add the devlog**

Create `vault/02-Devlog/2026-06/2026-06-07-mission-control-ui-revamp.md`:

```markdown
# Mission Control UI Revamp

Date: 2026-06-07

Status: MISSION_CONTROL_UI_REVAMP_COMPLETE

The dashboard was redesigned around the approved Mission Control v2 direction.

Implemented:
- Mission Brief landing page.
- Mission Control sidebar and section labels.
- Project Story, Strategy Builder, Portfolio Lab, Regime Playbook, Data Vault, and Decision Ledger routing.
- Human explanation panels before dense metrics and raw artifacts.
- Raw audit details moved behind explicit expanders where practical.

Governance:
- No provider query was performed.
- No market-data download was performed.
- No backtest was performed.
- No paper trading, live trading, or promotion state changed.

Verification:
- Python compile checks passed.
- Dashboard bootstrap tests passed.
- Mission Control UI tests passed.
- Browser smoke checks passed on the main Mission Control routes.
```

- [ ] **Step 2: Run final verification**

Run:

```powershell
.\.venv-lab\Scripts\python.exe -m py_compile dashboard\app.py dashboard\mission_control_ui.py
.\.venv-lab\Scripts\python.exe -m pytest tests\test_dashboard_app_bootstrap.py tests\test_mission_control_ui.py -q
```

Expected: all checks pass.

- [ ] **Step 3: Check git status**

Run:

```powershell
git status --short
```

Expected: only `dashboard/app.py`, `dashboard/mission_control_ui.py`, relevant tests, and the devlog are staged or modified for this implementation. Existing unrelated research artifacts may remain dirty and must not be included.

- [ ] **Step 4: Commit final devlog**

Run:

```powershell
git add vault/02-Devlog/2026-06/2026-06-07-mission-control-ui-revamp.md
git commit -m "Document Mission Control UI revamp"
```

- [ ] **Step 5: Push**

Run:

```powershell
git push
```

Expected: branch `main` pushes successfully.

---

## Self-Review

Spec coverage:

- Mission Brief: Task 3.
- Project Story: Task 4.
- Strategy Builder: Task 4 routes existing Workbench under the new label; Task 5 reduces raw-first output.
- Portfolio Lab: Task 4 routes it, Task 5 preserves guided setup/verdict/dynamic/audit structure.
- Regime Playbook: Task 4 introduces a route and explanation wrapper around existing regime data.
- Data Vault: Task 4 introduces a route and explanation wrapper around provider/data readiness.
- Decision Ledger: Task 4 introduces a route for raw audit review.
- Human explanation before dense content: Tasks 3, 4, and 5.
- Governance unchanged: Tasks 1-6 do not alter quant data builders or execution permissions.
- Verification: Task 6.

Placeholder scan:

- The plan contains no `TBD`, no incomplete scope sections, and no unspecified test command.

Type consistency:

- `MissionSection`, `MISSION_SECTIONS`, `build_mission_status`, `mission_section_by_label`, and `mission_sidebar_html` are defined in Task 1 and imported in Task 2.
- `SECTIONS` becomes a list of labels derived from `MISSION_SECTIONS`, matching the tests.
