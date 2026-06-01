# Portfolio Artifact Audit - 2026-06-01

## Purpose

This audit organizes previously untracked Portfolio Lab artifacts created during the Candidate 001 / Candidate 002 research sequence.

The artifacts are preserved because they form the chain of custody for the current portfolio-research state:

- local portfolio diagnostics
- preregistration drafts and approvals
- separate dry-run trials
- frozen recipe validations
- external-data gates
- manual composite manifests
- Candidate 001 vs Candidate 002 comparison

## Governance Status

These artifacts do **not** promote a strategy.

All preserved decisions remain diagnostic-only, data-gate-only, archive, or blocked states. The dominant blockers are:

- `factory_generated_scope_gate`
- `component_concentration_gate`
- `cost_stress_gate`
- `external_data_contract_gate`
- `iterative_search_after_candidate_001`

## Canonical Current State

Candidate 002 remains the active research-review target only because it improved validation behavior and reduced drawdown versus Candidate 001 in the local/proxy diagnostic surface.

Candidate 002 is not deployable. It is blocked until a non-synthetic PIT / survivorship-free data bundle exists.

The later true-backtest spec and mock admissible bundle explicitly prohibit:

- reusing Workbench proxy P&L
- paper trading
- live trading
- promotion
- financial performance claims from synthetic or proxy data

## Repository Hygiene Actions

- Preserved Portfolio Lab artifacts that document the research chain.
- Removed the empty local `_COMMUNITY_Community 2.md` placeholder from the workspace.
- Left the Graphify report unstaged because Git reports it as modified without a substantive content diff, consistent with a line-ending/working-tree normalization artifact.

## Interpretation

This commit is archival hygiene, not new research evidence.

The only valid next step toward a true backtest remains the external data bundle gate.
