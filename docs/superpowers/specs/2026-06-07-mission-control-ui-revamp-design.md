# Mission Control UI Revamp Design

Date: 2026-06-07

Status: Approved visual direction, pending implementation plan

## Goal

Redesign the Streamlit dashboard from a dense artifact console into a guided research operating system. The product should be understandable to someone who does not know the project, while still remaining useful for technical research work.

The approved direction is **Mission Control v2**: a technical control room with clear navigation, human explanations before technical panels, and raw audit data moved behind explicit advanced sections.

## Product Principle

Every screen must answer three questions before showing dense tables:

1. What am I looking at?
2. Why does it matter?
3. What can I do next?

The dashboard must never imply trading readiness. It remains a diagnostic and research UI: no live trading, no paper trading, no provider query, no promotion unless existing governance explicitly allows it.

## Information Architecture

The current top navigation will be reorganized into a Mission Control structure:

- **Mission Brief**: current state, current blocker, next action, major lab status.
- **Project Story**: the life of the project, ideas tested, why each failed or blocked, and what capabilities were built.
- **Strategy Builder**: guided strategy creation flow, replacing raw-first controls with a wizard-like path.
- **Portfolio Lab**: basket composition, factory search, dynamic regime switching, preregistration, and data gates.
- **Regime Playbook**: market regime explanation, which strategy families are allowed, reduced, blocked, or observe-only by regime.
- **Data Vault**: provider readiness, PIT/delisted requirements, Norgate/EODHD/FMP status, and true-backtest blockers.
- **Decision Ledger**: final decisions, raw audit tables, provider-query ledger, and artifact paths.

## Page Pattern

Each major page should follow the same hierarchy:

1. **Human explanation panel**: plain-language summary.
2. **Status/action strip**: current decision, blocker, next allowed action.
3. **Primary visualization**: one or two charts that explain the key idea.
4. **Guided controls**: simple grouped controls, not scattered widgets.
5. **Result interpretation**: verdict translated into plain English.
6. **Audit details expander**: raw tables, JSON, manifests, final decisions, file paths.

This keeps all content available while preventing the user from meeting the raw ledger first.

## Visual Direction

Use a clean technical control-room style:

- Light background, not full dark-terminal.
- White panels with soft borders and clear grouping.
- Blue for actions and selected navigation.
- Green/mint for valid evidence.
- Amber for cost, risk, and friction.
- Rose/red for blockers and governance refusal.
- Plum/purple for data scope and structure.

Typography should remain technical but readable. Existing `Instrument Sans` and `IBM Plex Mono` are acceptable, but large bodies of content should use the sans font; monospace should be reserved for labels, IDs, contracts, and compact metadata.

## Sidebar Navigation

The redesigned sidebar should be the primary information architecture, not just a section switcher.

Each nav item should include:

- A short label.
- A one-line explanation.
- A visual state for selected/current section.

The sidebar should include a persistent status card:

- Current mode: `RISK_REGIME_ENGINE_ONLY` or equivalent.
- Promotion count.
- Current blocker.
- Next gate.

## Mission Brief

The new first screen should be the onboarding layer for the lab.

It should show:

- Current mission: build portfolios that know when to stay quiet.
- Current blocker: admissible PIT/survivorship-free data.
- Current candidate: dynamic portfolio candidate/data-gate state if available.
- Fast actions:
  - Create a strategy.
  - Test a portfolio.
  - Read the project story.
  - Inspect data blockers.

This page should explain that a block is not a bug; it is the lab protecting the research process.

## Strategy Builder

The Strategy Builder should become a guided wizard:

- Step 1: idea and family.
- Step 2: universe and data availability.
- Step 3: holding period, cost model, and risk box.
- Step 4: pre-run gate and dry-run.
- Step 5: result interpretation and package/audit output.

Raw manifest JSON and trade tables should remain available only under audit expanders.

## Portfolio Lab

Portfolio Lab should be reframed as a recipe lab, not a wall of optimizer output.

Primary flow:

1. Select or generate candidate sleeves.
2. Show which sleeves are eligible and which are excluded because of missing data.
3. Run bounded governed search.
4. Explain the best basket in plain English.
5. Show static vs dynamic regime-switching comparison.
6. Create preregistration draft only after the user understands blockers.
7. Keep true backtest/data gates separate and visibly locked.

Automatic search must remain anti-overfit:

- Deduplicate equivalent strategies before search.
- Use fixed objective and bounded candidate size.
- Show validation net and ex-best metrics.
- Keep promotion locked.
- Exclude strategies that cannot be truly tested because data is missing.

## Regime Playbook

This should become the key educational page for dynamic allocation.

For each regime, show:

- What the regime means in plain language.
- Which sleeves are full-size, reduced, blocked, or observe-only.
- Why each family is routed that way.
- Historical local/proxy evidence, clearly labeled as non-promotable when applicable.

The goal is to explain when a strategy should live, shrink, or go quiet.

## Data Vault

Data Vault should make provider/data blockers understandable.

It should show:

- Required fields for true testing.
- Which provider can supply each field.
- Which fields are present locally.
- Which fields are still missing.
- Whether the bundle is admissible, partial, mock, or blocked.

The user should immediately understand why yfinance-like data is insufficient and why Kronos does not fix survivorship/PIT contamination.

## Error Handling And Empty States

Every empty or blocked state should include:

- What happened.
- Why it matters.
- What to do next.

Examples:

- No components available: guide user to Strategy Builder dry-run first.
- All components blocked by regime: suggest changing regime or adding a Regime Filter sleeve.
- Data gate blocked: list missing fields and possible provider paths.
- Dynamic underperforms static: explain that regime routing is not yet return-enhancing.

## Testing And Verification

Implementation should be verified with:

- Python compile check for `dashboard/app.py`.
- Existing dashboard bootstrap tests.
- Browser smoke checks for Mission Brief, Strategy Builder, Portfolio Lab, Regime Playbook, and Data Vault.
- Visual checks for:
  - no Streamlit traceback,
  - readable contrast,
  - no overlapped controls,
  - advanced tables collapsed by default,
  - primary actions visible without scrolling too far.

## Non-Goals

This revamp does not:

- Add live trading.
- Add paper trading.
- Run provider queries.
- Run true backtests.
- Change quant governance or promotion rules.
- Claim strategy profitability.

It is a product redesign around the existing research engine.
