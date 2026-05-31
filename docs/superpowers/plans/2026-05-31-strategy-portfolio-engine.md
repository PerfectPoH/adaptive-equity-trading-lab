# Strategy Portfolio Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first diagnostic-only Portfolio Lab engine that composes saved Strategy Workbench dry-runs into a governed portfolio diagnostic.

**Architecture:** Add a focused pure-Python engine under `src/experiments/workbench_portfolio_engine.py`, expose helper functions through `dashboard/lab_dashboard_data.py`, then render a new `Portfolio Lab` section in `dashboard/app.py`. Keep all portfolio runs local, artifact-based, non-promotable, and provider-free.

**Tech Stack:** Python, pandas, Plotly, Streamlit, pytest, existing Workbench artifact contracts.

---

### Task 1: Portfolio Engine Data Layer

**Files:**
- Create: `src/experiments/workbench_portfolio_engine.py`
- Test: `tests/test_workbench_portfolio_engine.py`

- [ ] **Step 1: Write failing tests for loading components and building a return matrix**

Create tests that build temporary Workbench-style artifact folders with `dry_run_result.json`, `trade_list.csv`, and `equity_curve.csv`, then assert the loader returns components and the return matrix has one column per component.

- [ ] **Step 2: Implement component loading**

Implement `load_workbench_portfolio_components(root: Path = Path("."), limit: int = 40) -> list[dict[str, Any]]`.

- [ ] **Step 3: Implement return normalization**

Implement `build_component_return_matrix(components: list[dict[str, Any]]) -> pd.DataFrame`, using equity curve differences when available and grouped trade returns as fallback.

- [ ] **Step 4: Run targeted tests**

Run: `.venv-lab\Scripts\python.exe -m pytest tests/test_workbench_portfolio_engine.py -q`

### Task 2: Allocation, Simulation, And Gates

**Files:**
- Modify: `src/experiments/workbench_portfolio_engine.py`
- Test: `tests/test_workbench_portfolio_engine.py`

- [ ] **Step 1: Write failing tests for allocation policies**

Cover equal weight, inverse volatility with caps, and sleeve allocation.

- [ ] **Step 2: Implement allocation policies**

Implement `build_portfolio_allocation(components, return_matrix, policy, max_component_weight, max_rejected_weight, max_convex_weight)`.

- [ ] **Step 3: Write failing tests for portfolio diagnostics and fragility gates**

Assert cost stress, ex-best-component, correlation, concentration, and data-contract gates are emitted.

- [ ] **Step 4: Implement simulation and gates**

Implement `run_portfolio_diagnostic(...) -> dict[str, Any]`.

- [ ] **Step 5: Run targeted tests**

Run: `.venv-lab\Scripts\python.exe -m pytest tests/test_workbench_portfolio_engine.py -q`

### Task 3: Artifact Writer And CLI Safety

**Files:**
- Modify: `src/experiments/workbench_portfolio_engine.py`
- Test: `tests/test_workbench_portfolio_engine.py`

- [ ] **Step 1: Write failing tests for persisted portfolio artifacts**

Assert the writer emits `portfolio_manifest.json`, `component_manifest.csv`, `component_return_matrix.csv`, `allocation_table.csv`, `portfolio_equity_curve.csv`, `portfolio_drawdown.csv`, `portfolio_correlation_matrix.csv`, `portfolio_gate_panel.json`, `portfolio_final_decision.json`, and `portfolio_vault_report.md`.

- [ ] **Step 2: Implement artifact writer**

Implement `persist_portfolio_diagnostic(...) -> dict[str, str]`.

- [ ] **Step 3: Implement CLI guardrails**

Add `main(argv=None) -> int` that blocks `--paper`, `--live`, `--promote`, `--provider-query`, and `--download-market-data`.

- [ ] **Step 4: Run targeted tests**

Run: `.venv-lab\Scripts\python.exe -m pytest tests/test_workbench_portfolio_engine.py -q`

### Task 4: Dashboard Integration

**Files:**
- Modify: `dashboard/lab_dashboard_data.py`
- Modify: `dashboard/app.py`
- Test: `tests/test_lab_dashboard_data.py`

- [ ] **Step 1: Add data-layer wrappers**

Expose component loading, portfolio preview, and artifact persistence helpers from `dashboard/lab_dashboard_data.py`.

- [ ] **Step 2: Add tests for dashboard helper availability**

Assert saved components can be loaded through dashboard helpers and portfolio preview contains verdict, charts, and gate rows.

- [ ] **Step 3: Add `Portfolio Lab` navigation**

Add `Portfolio Lab` to `SECTIONS`, implement `render_portfolio_lab()`, and route it from the main navigation.

- [ ] **Step 4: Use progressive UI disclosure**

Render thesis, component selector, allocation policy, result cards, equity/drawdown charts, contribution chart, correlation heatmap, gate table, and artifact persistence.

- [ ] **Step 5: Run dashboard tests**

Run: `.venv-lab\Scripts\python.exe -m pytest tests/test_lab_dashboard_data.py tests/test_workbench_portfolio_engine.py -q`

### Task 5: Verification And Commit

**Files:**
- Modify: generated source/test/docs files only

- [ ] **Step 1: Run full test suite**

Run: `.venv-lab\Scripts\python.exe -m pytest -q`

- [ ] **Step 2: Verify Streamlit imports**

Run: `.venv-lab\Scripts\python.exe -m py_compile dashboard\app.py dashboard\lab_dashboard_data.py src\experiments\workbench_portfolio_engine.py`

- [ ] **Step 3: Review git diff**

Run: `git diff --stat` and ensure unrelated dirty files remain untouched.

- [ ] **Step 4: Commit and push**

Commit message: `Add diagnostic strategy portfolio engine`

