from __future__ import annotations

from html import escape
import json
import math
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    WORKBENCH_TEMPLATES,
    build_controlled_backtest_preview,
    build_strategy_chart_story,
    build_workbench_chart_story,
    build_workbench_rule_flow,
    build_workbench_trade_annotation_story,
    build_workbench_data_scope_preview,
    build_workbench_flow_nodes,
    build_workbench_manifest,
    build_workbench_pre_run_gate,
    build_workbench_backtest_readiness,
    build_workbench_strategy_package,
    build_workbench_comparison_table,
    delisted_data_source_gate_payload,
    governance_metrics,
    load_dashboard_payload,
    persist_workbench_run_bundle,
    persist_workbench_strategy_package,
    project_capability_rows,
    project_lifecycle_rows,
    strategy_detail,
    strategy_rows,
    validate_workbench_manifest,
    workbench_gate_is_valid,
    workbench_manifest_signature,
    build_workbench_result_summary,
    build_workbench_strategy_narrative,
    build_workbench_strategy_blueprint,
    build_workbench_metric_glossary,
    build_workbench_visual_diagnostics,
    build_factory_data_eligibility_report,
    build_portfolio_lab_preview,
    build_portfolio_lab_preview_from_components,
    build_regime_aware_portfolio_component_set,
    build_regime_switching_portfolio_diagnostic,
    build_portfolio_preregistration_approval_gate,
    build_portfolio_preregistration_draft,
    build_portfolio_frozen_recipe_trial,
    build_portfolio_external_data_backtest_gate,
    build_portfolio_manual_composite_trial,
    build_portfolio_candidate_primary_research_state,
    build_portfolio_candidate_true_backtest_harness,
    build_portfolio_candidate_true_backtest_spec,
    build_portfolio_manual_partial_data_bundle,
    build_portfolio_mock_admissible_data_bundle,
    build_separate_portfolio_trial_dry_run,
    build_strategy_factory_components,
    display_safe_records,
    load_workbench_strategy_cards,
    load_workbench_strategy_packages,
    load_portfolio_candidate_primary_research_state,
    load_portfolio_lab_components,
    inspect_workbench_strategy_package,
    materialize_factory_components_as_workbench_runs,
    persist_portfolio_lab_preview,
    persist_portfolio_preregistration_approval_gate,
    persist_portfolio_preregistration_draft,
    persist_portfolio_frozen_recipe_trial,
    persist_portfolio_external_data_backtest_gate,
    persist_portfolio_manual_composite_trial,
    persist_portfolio_candidate_primary_research_state,
    persist_portfolio_candidate_true_backtest_spec,
    persist_portfolio_manual_partial_data_bundle,
    persist_portfolio_mock_admissible_data_bundle,
    persist_separate_portfolio_trial_dry_run,
    portfolio_lab_component_table,
    run_portfolio_candidate_true_backtest_skeleton,
)
from dashboard.mission_control_ui import (
    MISSION_SECTIONS,
    build_mission_status,
    mission_section_by_label,
    mission_sidebar_html,
)
from src.experiments.workbench_package_runner import run_package_diagnostic


st.set_page_config(page_title="Adaptive Equity Trading Lab", layout="wide", initial_sidebar_state="expanded")

SECTIONS = [section.label for section in MISSION_SECTIONS]
COLOR_LOGIC = {
    "Blue": {
        "css": "#1f5eff",
        "title": "Signal and action",
        "body": "Blue marks the place where the user or strategy does something: entry logic, selected navigation, primary buttons, and live chart annotations.",
    },
    "Mint": {
        "css": "#0f9f75",
        "title": "Evidence that survived",
        "body": "Mint marks facts the lab can actually support: valid local coverage, completed checks, documented evidence, and results that are safe to inspect.",
    },
    "Amber": {
        "css": "#d97706",
        "title": "Risk, cost, and friction",
        "body": "Amber marks the parts that usually kill paper alpha: transaction costs, slippage, fragile assumptions, and unresolved operating risk.",
    },
    "Plum": {
        "css": "#7c3aed",
        "title": "Data scope and structure",
        "body": "Plum marks the research container: universe routing, dataset scope, provider boundaries, and the difference between local data and missing coverage.",
    },
    "Rose": {
        "css": "#d12f5f",
        "title": "Blockers and fragility",
        "body": "Rose marks the lab saying no: PIT blockers, survivorship bias, outlier dependency, insufficient sample size, or promotion locked false.",
    },
}


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
        :root {
          --lab-bg: #fbfaf7;
          --lab-panel: #ffffff;
          --lab-ink: #3f3f46;
          --lab-strong: #171717;
          --lab-muted: #71717a;
          --lab-blue: #1f5eff;
          --lab-blue-2: #3b82f6;
          --lab-blue-soft: #eef3ff;
          --lab-amber: #d97706;
          --lab-amber-soft: #fff7ed;
          --lab-plum: #7c3aed;
          --lab-plum-soft: #f3edff;
          --lab-mint: #0f9f75;
          --lab-mint-soft: #e9fbf4;
          --lab-rose: #d12f5f;
          --lab-rose-soft: #fff0f5;
          --lab-line: #e7e2d8;
          --lab-line-strong: #cfc7bb;
          --lab-red: #b42318;
          --lab-green: #0f8a4b;
          --lab-slate: #171717;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {
          display: none !important;
          visibility: hidden !important;
        }
        html, body, [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(circle at 88% 6%, rgba(31,94,255,.08), transparent 26%),
            radial-gradient(circle at 8% 28%, rgba(15,159,117,.075), transparent 28%),
            linear-gradient(90deg, rgba(231,226,216,.55) 1px, transparent 1px),
            var(--lab-bg);
          background-size: auto, auto, 72px 72px;
          background-position: 0 0, 0 0, 0 0;
          color: var(--lab-ink);
          font-family: "Instrument Sans", system-ui, sans-serif;
          animation: labGridDrift 28s linear infinite;
        }
        section[data-testid="stSidebar"] {
          background: rgba(251, 250, 247, .94);
          border-right: 1px solid var(--lab-line);
          min-width: 310px;
        }
        section[data-testid="stSidebar"] * {
          color: var(--lab-ink);
        }
        section[data-testid="stSidebar"] .sidebar-tile {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: rgba(255, 255, 255, .78);
          padding: 14px;
          min-height: 108px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 12px 34px rgba(23,23,23,.055);
        }
        section[data-testid="stSidebar"] .sidebar-label {
          color: var(--lab-blue) !important;
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
        }
        section[data-testid="stSidebar"] .sidebar-value {
          color: var(--lab-strong) !important;
          font-family: "Instrument Sans", system-ui, sans-serif;
          font-size: 30px;
          font-weight: 800;
          line-height: 1.05;
          overflow-wrap: anywhere;
        }
        section[data-testid="stSidebar"] .sidebar-note {
          color: var(--lab-muted) !important;
          font-size: 13px;
          line-height: 1.35;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          margin-bottom: 8px;
          padding: 9px 11px;
          background: rgba(255,255,255,.72);
          cursor: pointer;
          transition: transform .18s ease, background .18s ease, border-color .18s ease, box-shadow .18s ease;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
          background: #ffffff;
          border-color: #93c5fd;
          box-shadow: 0 10px 28px rgba(37,99,235,.10);
          transform: translateX(2px);
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
          background: #2563eb;
          border-color: #2563eb;
          box-shadow: 0 16px 34px rgba(37,99,235,.22);
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
        section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span {
          color: #ffffff !important;
        }
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
          margin-top: 6px;
          text-transform: uppercase;
        }
        .mc-nav-item {
          background: transparent;
          border: 1px solid transparent;
          border-radius: 12px;
          padding: 10px 11px;
        }
        .mc-nav-item.active {
          background: #eff6ff;
          border-color: #bfdbfe;
        }
        .mc-nav-item strong {
          color: #0f172a;
          display: block;
          font-size: 14px;
        }
        .mc-nav-item.active strong {
          color: #1d4ed8;
        }
        .mc-nav-item span {
          color: #64748b;
          display: block;
          font-size: 12px;
          line-height: 1.35;
          margin-top: 3px;
        }
        .mc-status-card {
          background: #0f172a;
          border-radius: 16px;
          color: #ffffff;
          padding: 14px;
        }
        .mc-status-card span,
        .mc-status-card small,
        .mc-status-card em {
          color: #cbd5e1;
          display: block;
          font-size: 12px;
          font-style: normal;
          line-height: 1.4;
        }
        .mc-status-card strong {
          color: #ffffff;
          display: block;
          font-size: 21px;
          line-height: 1.05;
          margin: 6px 0;
          overflow-wrap: anywhere;
        }
        .mission-brief-hero {
          background: linear-gradient(135deg, rgba(37,99,235,.96), rgba(15,23,42,.98) 58%, rgba(217,119,6,.78));
          border: 1px solid #1e293b;
          border-radius: 24px;
          box-shadow: 0 24px 70px rgba(15,23,42,.15);
          color: #ffffff;
          padding: 36px;
        }
        .mission-brief-hero h1 {
          color: #ffffff;
          font-size: clamp(42px, 5vw, 68px);
          letter-spacing: -.04em;
          line-height: .95;
          margin: 10px 0 14px;
        }
        .mission-brief-hero p {
          color: #dbeafe !important;
          font-size: 17px;
          line-height: 1.58;
          max-width: 880px;
        }
        h1, h2, h3 {
          font-family: "Instrument Sans", system-ui, sans-serif;
          letter-spacing: -.025em;
          color: var(--lab-strong);
        }
        .block-container {
          padding-top: 1.05rem;
          padding-bottom: 5rem;
          max-width: 1420px;
        }
        .block-container > div {
          animation: labFadeUp .42s ease both;
        }
        .lab-shell-nav {
          position: sticky;
          top: 0;
          z-index: 50;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          border: 1px solid var(--lab-line);
          border-radius: 9px;
          background: rgba(255, 255, 255, .78);
          backdrop-filter: blur(12px);
          padding: 12px 14px;
          margin-bottom: 22px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 16px 46px rgba(23,23,23,.055);
        }
        .main-nav-card {
          border: 1px solid var(--lab-line);
          border-radius: 9px;
          background: rgba(255,255,255,.72);
          padding: 14px;
          margin-bottom: 30px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 16px 46px rgba(23,23,23,.045);
        }
        .nav-help {
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          color: var(--lab-muted);
          margin-bottom: 8px;
          text-transform: uppercase;
          font-weight: 700;
        }
        div[data-testid="stButton"] > button {
          border-radius: 8px;
          border: 1px solid var(--lab-line);
          font-weight: 700;
          min-height: 44px;
          transition: background .18s ease, border-color .18s ease, transform .18s ease;
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
          background: #ffffff;
          color: #0f172a;
          border-color: #94a3b8;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
          background: #eff6ff;
          color: #1d4ed8;
          border-color: #2563eb;
          transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button[kind="primary"] {
          background: #2563eb;
          color: #ffffff;
          border-color: #2563eb;
        }
        .main-nav-card div[data-testid="stButton"] > button[kind="secondary"] {
          background: #ffffff;
          color: #1e293b;
          border-color: #cbd5e1;
        }
        .main-nav-card div[data-testid="stButton"] > button[kind="secondary"]:hover {
          background: #f8fafc;
          color: #1d4ed8;
          border-color: #93c5fd;
        }
        div[data-testid="stButton"] > button * {
          color: inherit !important;
        }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stSlider"] label,
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[data-testid="stMarkdownContainer"] p {
          color: #0f172a;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
          background: #ffffff;
          color: #0f172a;
          border: 1px solid #cbd5e1;
          border-radius: 8px;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] svg {
          color: #0f172a;
          fill: #0f172a;
        }
        div[data-testid="stTextArea"] textarea::placeholder,
        div[data-testid="stTextInput"] input::placeholder {
          color: #64748b;
          opacity: 1;
        }
        div[data-testid="stRadio"] [role="radiogroup"] label {
          background: transparent;
          border: 0;
          color: #0f172a;
        }
        div[data-testid="stRadio"] [role="radiogroup"] label span,
        div[data-testid="stRadio"] [role="radiogroup"] label p {
          color: #0f172a;
          font-weight: 600;
        }
        div[data-testid="stTabs"] button {
          color: #334155;
          font-weight: 750;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
          color: var(--lab-blue);
        }
        div[data-testid="stExpander"] {
          border: 1px solid var(--lab-line);
          border-radius: 10px;
          background: rgba(255,255,255,.74);
          margin: 14px 0;
        }
        div[data-testid="stExpander"] summary p {
          color: #0f172a;
          font-weight: 750;
        }
        div[data-testid="stDataFrame"] {
          border-radius: 10px;
          overflow: hidden;
          margin-top: 8px;
          margin-bottom: 18px;
        }
        div[data-testid="stPlotlyChart"] {
          background: #ffffff;
          border: 1px solid var(--lab-line);
          border-radius: 12px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 42px rgba(23,23,23,.055);
          overflow: hidden;
          margin-top: 8px;
          margin-bottom: 26px;
          padding: 10px;
          transition: transform .18s ease, box-shadow .18s ease;
        }
        div[data-testid="stPlotlyChart"]:hover {
          transform: translateY(-2px);
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 26px 58px rgba(23,23,23,.08);
        }
        div[data-testid="stPlotlyChart"] .modebar {
          display: none !important;
        }
        div[data-testid="stPlotlyChart"] .main-svg {
          background: #ffffff !important;
        }
        div[data-testid="stPlotlyChart"] .xtick text,
        div[data-testid="stPlotlyChart"] .ytick text,
        div[data-testid="stPlotlyChart"] .gtitle,
        div[data-testid="stPlotlyChart"] .xtitle,
        div[data-testid="stPlotlyChart"] .ytitle,
        div[data-testid="stPlotlyChart"] .legendtext,
        div[data-testid="stPlotlyChart"] .annotation-text {
          fill: #0f172a !important;
          opacity: 1 !important;
        }
        div[data-testid="stPlotlyChart"] .gridlayer path {
          stroke: #d5dbe5 !important;
          opacity: .85 !important;
        }
        .router-matrix-shell {
          background: #ffffff;
          border: 1px solid var(--lab-line);
          border-radius: 14px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 42px rgba(23,23,23,.055);
          margin: 10px 0 22px;
          overflow-x: auto;
          padding: 14px;
        }
        .router-matrix {
          display: grid;
          grid-template-columns: minmax(150px, .9fr) repeat(var(--regime-count), minmax(92px, 1fr));
          gap: 8px;
          min-width: min(100%, 760px);
        }
        .router-corner,
        .router-header,
        .router-family,
        .router-cell {
          border-radius: 10px;
          min-height: 54px;
          padding: 10px;
        }
        .router-corner,
        .router-header {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          color: #334155;
          font-family: "IBM Plex Mono", monospace;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: .04em;
          overflow-wrap: anywhere;
          text-transform: uppercase;
        }
        .router-family {
          align-items: center;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          color: #0f172a;
          display: flex;
          font-weight: 800;
          line-height: 1.2;
        }
        .router-cell {
          border: 1px solid transparent;
          box-shadow: inset 0 1px 0 rgba(255,255,255,.36);
          color: #ffffff;
          display: grid;
          gap: 4px;
          transition: transform .18s ease, box-shadow .18s ease;
        }
        .router-cell:hover {
          box-shadow: 0 16px 34px rgba(15,23,42,.16);
          transform: translateY(-2px);
        }
        .router-cell strong {
          color: #ffffff;
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          letter-spacing: .02em;
          line-height: 1.15;
          overflow-wrap: anywhere;
        }
        .router-cell small {
          color: rgba(255,255,255,.86);
          font-size: 11px;
          line-height: 1.25;
        }
        .router-cell.block {
          background: linear-gradient(135deg, #be123c, #d12f5f);
        }
        .router-cell.reduce {
          background: linear-gradient(135deg, #b45309, #d97706);
        }
        .router-cell.proxy {
          background: linear-gradient(135deg, #1d4ed8, #1f5eff);
        }
        .router-cell.overlay,
        .router-cell.allow {
          background: linear-gradient(135deg, #047857, #0f9f75);
        }
        .router-cell.observe {
          background: linear-gradient(135deg, #6d28d9, #7c3aed);
        }
        div[data-testid="stSlider"] [data-testid="stTickBar"] {
          color: #334155;
        }
        .lab-brand {
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          font-weight: 700;
          color: var(--lab-blue);
          text-transform: uppercase;
        }
        .lab-nav-state {
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          color: var(--lab-muted);
        }
        .lab-hero {
          position: relative;
          overflow: hidden;
          border: 1px solid #1f2937;
          border-radius: 12px;
          background:
            radial-gradient(circle at 82% 18%, rgba(15,159,117,.35), transparent 25%),
            linear-gradient(115deg, rgba(31, 94, 255, .98), rgba(23, 23, 23, .98) 55%, rgba(217, 119, 6, .78)),
            #171717;
          padding: 44px 42px 36px;
          margin-bottom: 28px;
          color: #f8fafc;
          min-height: 320px;
          box-shadow: 0 1px 0 rgba(23,23,23,.08), 0 24px 70px rgba(23,23,23,.14);
        }
        .lab-hero::after {
          content: "";
          position: absolute;
          inset: auto 0 0 0;
          height: 110px;
          background-image:
            linear-gradient(90deg, rgba(255,255,255,.10) 1px, transparent 1px),
            linear-gradient(0deg, rgba(255,255,255,.08) 1px, transparent 1px);
          background-size: 42px 28px;
          opacity: .52;
        }
        .lab-kicker {
          font-family: "IBM Plex Mono", monospace;
          color: #bfdbfe;
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: .06em;
        }
        .lab-title {
          position: relative;
          z-index: 1;
          font-family: "Instrument Sans", system-ui, sans-serif;
          font-size: clamp(42px, 6vw, 78px);
          letter-spacing: -.05em;
          line-height: .92;
          font-weight: 800;
          max-width: 1000px;
          margin: 12px 0;
          color: #ffffff;
        }
        .lab-subtitle {
          position: relative;
          z-index: 1;
          max-width: 940px;
          color: #dbeafe;
          font-size: 18px;
          line-height: 1.55;
        }
        .metric-card, .strategy-card, .lab-section, .chart-panel {
          border: 1px solid var(--lab-line);
          border-radius: 9px;
          background: rgba(255,255,255,.84);
          padding: 18px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 16px 46px rgba(23,23,23,.055);
        }
        .metric-label, .strategy-family, .eyebrow {
          color: var(--lab-muted);
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: .04em;
        }
        .metric-value {
          color: var(--lab-strong);
          font-family: "Instrument Sans", system-ui, sans-serif;
          font-size: 32px;
          font-weight: 800;
          margin-top: 4px;
          overflow-wrap: anywhere;
          line-height: 1.1;
        }
        .metric-value-long {
          font-size: 22px;
        }
        .metric-note, .small-muted {
          color: var(--lab-muted);
          font-size: 13px;
          line-height: 1.45;
        }
        .status-pill {
          display: inline-flex;
          align-items: center;
          width: fit-content;
          border-radius: 999px;
          padding: 5px 10px;
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          font-weight: 700;
          border: 1px solid var(--lab-line);
          background: #f1f5f9;
        }
        .status-ARCHIVED { color: #92400e; background: #ffedd5; border-color: #fed7aa; }
        .status-BLOCKED { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .status-DIAGNOSTIC { color: #1d4ed8; background: #dbeafe; border-color: #bfdbfe; }
        .status-NOT-RUN { color: #475569; background: #f1f5f9; }
        .status-PROMOTED { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
        .strategy-section {
          border: 1px solid var(--lab-line);
          border-radius: 12px;
          background:
            linear-gradient(180deg, rgba(255,255,255,.88), rgba(255,255,255,.98)),
            #ffffff;
          padding: 28px;
          margin: 32px 0;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 52px rgba(23,23,23,.06);
        }
        .strategy-title {
          font-family: "Instrument Sans", system-ui, sans-serif;
          font-size: clamp(26px, 3vw, 40px);
          font-weight: 800;
          margin: 8px 0 6px;
          color: var(--lab-strong);
        }
        .strategy-copy {
          color: var(--lab-ink);
          line-height: 1.58;
          font-size: 15px;
        }
        .callout {
          border: 1px solid #c8d7ff;
          border-left: 4px solid var(--lab-blue);
          background: #eff6ff;
          padding: 14px 16px;
          border-radius: 8px;
          color: #1e3a8a;
          margin: 16px 0;
        }
        .danger-callout {
          border-left-color: var(--lab-red);
          background: #fef2f2;
          color: #7f1d1d;
        }
        .amber-callout {
          border-color: #fed7aa;
          border-left-color: var(--lab-amber);
          background: #fff7ed;
          color: #7c2d12;
        }
        .compact-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
          gap: 12px;
        }
        .page-guide {
          border: 1px solid var(--lab-line);
          border-radius: 12px;
          background: rgba(255,255,255,.82);
          padding: 18px;
          margin: -12px 0 30px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(23,23,23,.05);
        }
        .page-guide-title {
          color: var(--lab-strong);
          font-size: 22px;
          font-weight: 850;
          letter-spacing: -.02em;
          margin-bottom: 6px;
        }
        .page-guide-copy {
          color: var(--lab-muted);
          line-height: 1.55;
          max-width: 920px;
        }
        .guide-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
          margin-top: 16px;
        }
        .guide-card {
          border: 1px solid var(--lab-line);
          border-left: 4px solid var(--lab-blue);
          border-radius: 10px;
          background: #fff;
          padding: 14px;
          min-height: 116px;
        }
        .guide-card.good { border-left-color: var(--lab-mint); }
        .guide-card.warn { border-left-color: var(--lab-amber); }
        .guide-card.block { border-left-color: var(--lab-rose); }
        .guide-card.data { border-left-color: var(--lab-plum); }
        .guide-title {
          color: var(--lab-strong);
          font-weight: 850;
          margin-bottom: 6px;
        }
        .guide-copy {
          color: var(--lab-ink);
          font-size: 14px;
          line-height: 1.45;
        }
        .clean-panel {
          border: 1px solid var(--lab-line);
          border-radius: 12px;
          background: rgba(255,255,255,.76);
          padding: 20px;
          margin: 18px 0 28px;
          box-shadow: 0 1px 0 rgba(23,23,23,.035), 0 16px 44px rgba(23,23,23,.045);
        }
        .section-note {
          border: 1px solid #bfdbfe;
          border-left: 4px solid var(--lab-blue);
          background: #eff6ff;
          color: #1e3a8a;
          border-radius: 10px;
          padding: 14px 16px;
          margin: 12px 0 22px;
          line-height: 1.5;
        }
        .mini-tile {
          border: 1px solid var(--lab-line);
          border-radius: 9px;
          background: rgba(255,255,255,.82);
          padding: 14px;
          min-height: 108px;
          box-shadow: 0 1px 0 rgba(23,23,23,.035);
        }
        .lifecycle-card {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: #ffffff;
          padding: 18px;
          min-height: 230px;
          box-shadow: 0 14px 34px rgba(15, 23, 42, .05);
        }
        .lifecycle-phase {
          font-family: "Exo", system-ui, sans-serif;
          font-size: 22px;
          font-weight: 800;
          color: var(--lab-strong);
          margin: 8px 0;
        }
        .lifecycle-source {
          display: inline-flex;
          border: 1px solid #bfdbfe;
          background: #eff6ff;
          color: #1d4ed8;
          border-radius: 999px;
          padding: 4px 9px;
          font-family: "Roboto Mono", monospace;
          font-size: 11px;
          font-weight: 700;
        }
        .results-spacer {
          height: 28px;
        }
        .capability-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 12px;
        }
        .capability {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: #fff;
          padding: 14px;
          min-height: 120px;
        }
        .workbench-card {
          border: 1px solid var(--lab-line);
          border-radius: 10px;
          background: rgba(255,255,255,.86);
          padding: 22px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(23,23,23,.06);
        }
        .workbench-step {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 26px;
          height: 26px;
          border-radius: 999px;
          background: var(--lab-blue);
          color: #ffffff;
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          font-weight: 800;
          margin-right: 8px;
        }
        .dryrun-report {
          border: 1px solid #c8d7ff;
          border-top: 4px solid var(--lab-blue);
          border-radius: 10px;
          background: rgba(255,255,255,.88);
          padding: 22px;
          margin-top: 18px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(31, 94, 255, .08);
        }
        .dryrun-title {
          font-family: "Instrument Sans", system-ui, sans-serif;
          color: #0f172a;
          font-size: 26px;
          font-weight: 800;
          margin-bottom: 6px;
        }
        .dryrun-meta {
          color: #334155;
          font-size: 14px;
          line-height: 1.5;
        }
        .dryrun-list {
          margin: 0;
          padding-left: 18px;
          color: #334155;
          line-height: 1.55;
        }
        .rule-card {
          border: 1px solid var(--lab-line);
          border-top: 4px solid var(--lab-blue);
          border-radius: 10px;
          background: rgba(255,255,255,.86);
          padding: 16px;
          min-height: 120px;
          box-shadow: 0 1px 0 rgba(23,23,23,.035);
        }
        .rule-title {
          font-family: "Instrument Sans", system-ui, sans-serif;
          color: #0f172a;
          font-weight: 800;
          font-size: 18px;
          margin-bottom: 6px;
        }
        .validation-pass {
          border-top-color: var(--lab-mint);
          border-left: 4px solid var(--lab-mint);
          background: var(--lab-mint-soft);
          color: #14532d;
        }
        .validation-warn {
          border-top-color: var(--lab-amber);
          border-left: 4px solid var(--lab-amber);
          background: var(--lab-amber-soft);
          color: #7c2d12;
        }
        .validation-block {
          border-top-color: var(--lab-rose);
          border-left: 4px solid var(--lab-rose);
          background: var(--lab-rose-soft);
          color: #7f1d1d;
        }
        .human-workbench-hero {
          display: grid;
          grid-template-columns: minmax(0, 1.35fr) 380px;
          gap: 28px;
          align-items: stretch;
          margin: 12px 0 34px;
        }
        .human-workbench-copy {
          border: 1px solid #1f2937;
          border-radius: 12px;
          padding: 38px;
          min-height: 280px;
          color: white;
          background:
            radial-gradient(circle at 82% 18%, rgba(15,159,117,.33), transparent 25%),
            linear-gradient(120deg, rgba(31,94,255,.97), rgba(23,23,23,.98) 56%, rgba(217,119,6,.76)),
            #171717;
          box-shadow: 0 1px 0 rgba(23,23,23,.08), 0 24px 70px rgba(23,23,23,.14);
        }
        .human-workbench-copy h1 {
          color: #ffffff;
          font-size: clamp(46px, 6vw, 78px);
          line-height: .9;
          letter-spacing: 0;
          margin: 12px 0 16px;
          max-width: 820px;
        }
        .human-workbench-copy p {
          color: #eff6ff !important;
          font-size: 17px;
          line-height: 1.62;
          max-width: 780px;
          text-shadow: 0 1px 14px rgba(0,0,0,.36);
        }
        .human-workbench-note {
          border: 1px solid var(--lab-line);
          border-top: 4px solid var(--lab-mint);
          border-radius: 10px;
          background: rgba(255,255,255,.82);
          padding: 22px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(23,23,23,.06);
        }
        .portfolio-hero {
          display: grid;
          grid-template-columns: minmax(0, 1.45fr) minmax(280px, .55fr);
          gap: 22px;
          align-items: end;
          border: 1px solid #1e293b;
          border-radius: 12px;
          padding: 42px;
          margin: 12px 0 34px;
          color: #fff;
          background:
            linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px),
            linear-gradient(0deg, rgba(255,255,255,.07) 1px, transparent 1px),
            radial-gradient(circle at 75% 16%, rgba(15,159,117,.30), transparent 26%),
            linear-gradient(125deg, #1f5eff 0%, #172033 52%, #945100 100%);
          background-size: 38px 38px, 38px 38px, auto, auto;
          box-shadow: 0 1px 0 rgba(23,23,23,.08), 0 24px 70px rgba(23,23,23,.14);
        }
        .portfolio-hero h1 {
          color: #ffffff;
          font-size: clamp(44px, 6vw, 74px);
          line-height: .92;
          letter-spacing: 0;
          margin: 12px 0 16px;
          max-width: 900px;
        }
        .portfolio-hero p {
          color: #eaf2ff !important;
          font-size: 17px;
          line-height: 1.58;
          max-width: 880px;
          text-shadow: 0 1px 14px rgba(0,0,0,.28);
        }
        .portfolio-hero-note {
          border: 1px solid rgba(255,255,255,.24);
          border-radius: 10px;
          background: rgba(15,23,42,.36);
          padding: 18px;
          color: #f8fafc;
          backdrop-filter: blur(10px);
        }
        .portfolio-hero-note strong {
          display: block;
          color: #ffffff;
          font-size: 20px;
          margin-bottom: 8px;
        }
        .portfolio-hero-note span {
          color: #dbeafe;
          line-height: 1.45;
        }
        .portfolio-proof-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 14px;
          margin: 14px 0 24px;
        }
        .portfolio-proof-card {
          border: 1px solid var(--lab-line);
          border-top: 4px solid var(--lab-blue);
          border-radius: 10px;
          background: rgba(255,255,255,.88);
          padding: 16px;
          min-height: 132px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 16px 44px rgba(23,23,23,.05);
        }
        .portfolio-proof-card.warn { border-top-color: var(--lab-amber); }
        .portfolio-proof-card.good { border-top-color: var(--lab-mint); }
        .portfolio-proof-card.block { border-top-color: var(--lab-rose); }
        .portfolio-proof-title {
          color: var(--lab-strong);
          font-weight: 800;
          font-size: 18px;
          margin: 5px 0;
        }
        .portfolio-proof-copy {
          color: var(--lab-ink);
          font-size: 14px;
          line-height: 1.5;
        }
        .semantic-strip {
          display: flex;
          gap: 8px;
          margin-top: 18px;
        }
        .semantic-strip span {
          height: 10px;
          flex: 1;
          border-radius: 999px;
        }
        .color-meaning-card {
          border: 1px solid var(--lab-line);
          border-radius: 10px;
          background: rgba(255,255,255,.86);
          padding: 18px;
          box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(23,23,23,.05);
          margin: -18px 0 34px;
        }
        .color-meaning-row {
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }
        .color-dot-large {
          width: 18px;
          height: 18px;
          border-radius: 999px;
          flex: 0 0 auto;
          box-shadow: 0 0 0 5px rgba(23,23,23,.05);
          margin-top: 4px;
        }
        .color-meaning-title {
          color: var(--lab-strong);
          font-size: 18px;
          font-weight: 800;
          margin-bottom: 4px;
        }
        .color-meaning-body {
          color: var(--lab-ink);
          line-height: 1.56;
          max-width: 820px;
        }
        .semantic-badge {
          display: inline-flex;
          align-items: center;
          width: fit-content;
          border-radius: 999px;
          border: 1px solid var(--lab-line);
          padding: 6px 10px;
          font-family: "IBM Plex Mono", monospace;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
        }
        .badge-signal { background: var(--lab-blue-soft); color: var(--lab-blue); border-color: #c8d7ff; }
        .badge-evidence { background: var(--lab-mint-soft); color: var(--lab-mint); border-color: #b8efd9; }
        .badge-risk { background: var(--lab-amber-soft); color: var(--lab-amber); border-color: #fed7aa; }
        .badge-data { background: var(--lab-plum-soft); color: var(--lab-plum); border-color: #ddd6fe; }
        .badge-block { background: var(--lab-rose-soft); color: var(--lab-rose); border-color: #ffd1df; }
        .workbench-section {
          border-top: 1px solid var(--lab-line-strong);
          padding-top: 30px;
          margin-top: 52px;
        }
        .section-kicker {
          font-family: "IBM Plex Mono", monospace;
          color: var(--lab-muted);
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: .05em;
        }
        .workbench-section-title {
          font-size: 28px;
          font-weight: 800;
          letter-spacing: -.03em;
          margin: 4px 0 6px;
          color: var(--lab-strong);
        }
        .workbench-section-copy {
          color: var(--lab-ink);
          line-height: 1.62;
          max-width: 780px;
          margin-bottom: 18px;
        }
        div[data-testid="stMetric"] {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          padding: 12px;
          background: #fff;
        }
        @keyframes labFadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes labGridDrift {
          from { background-position: 0 0, 0 0, 0 0; }
          to { background-position: 18px 10px, -14px 8px, 72px 72px; }
        }
        @media (prefers-reduced-motion: reduce) {
          html, body, [data-testid="stAppViewContainer"],
          .block-container > div,
          div[data-testid="stPlotlyChart"],
          div[data-testid="stButton"] > button,
          section[data-testid="stSidebar"] [role="radiogroup"] label {
            animation: none !important;
            transition: none !important;
            transform: none !important;
          }
        }
        @media (max-width: 768px) {
          .lab-hero { padding: 24px; min-height: 260px; }
          .lab-title { font-size: 42px; }
          .lab-shell-nav { position: relative; align-items: flex-start; flex-direction: column; }
          .human-workbench-hero { grid-template-columns: 1fr; }
          .human-workbench-copy { padding: 26px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    css = status.replace(" ", "-")
    return f'<span class="status-pill status-{css}">{status}</span>'


def color_logic_component_html() -> str:
    payload = json.dumps(COLOR_LOGIC)
    return f"""
    <!doctype html>
    <html>
      <head>
        <style>
          body {{
            margin: 0;
            font-family: "Instrument Sans", Inter, system-ui, sans-serif;
            color: #171717;
            background: transparent;
          }}
          .card {{
            box-sizing: border-box;
            min-height: 318px;
            border: 1px solid #d8d2c8;
            border-top: 4px solid #0f9f75;
            border-radius: 10px;
            background: rgba(255,255,255,.88);
            padding: 22px;
            box-shadow: 0 1px 0 rgba(23,23,23,.04), 0 18px 54px rgba(23,23,23,.06);
          }}
          .eyebrow {{
            color: #675f55;
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
          }}
          h2 {{
            margin: 12px 0 8px;
            font-size: 24px;
            line-height: 1.12;
            letter-spacing: 0;
          }}
          p {{
            margin: 0;
            color: #3f3a34;
            font-size: 15px;
            line-height: 1.55;
          }}
          .strip {{
            display: flex;
            gap: 8px;
            margin: 18px 0 22px;
          }}
          button {{
            height: 10px;
            flex: 1;
            border: 0;
            border-radius: 999px;
            cursor: pointer;
            outline: 2px solid transparent;
            outline-offset: 4px;
            transition: transform .16s ease, outline-color .16s ease, box-shadow .16s ease;
          }}
          button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(23,23,23,.12);
          }}
          button[aria-pressed="true"] {{
            outline-color: currentColor;
            box-shadow: 0 0 0 4px rgba(255,255,255,.9), 0 10px 22px rgba(23,23,23,.14);
          }}
          .meaning {{
            display: grid;
            grid-template-columns: 18px 1fr;
            gap: 12px;
            border-top: 1px solid #e7e2d8;
            padding-top: 16px;
          }}
          .dot {{
            width: 18px;
            height: 18px;
            border-radius: 999px;
            margin-top: 3px;
            box-shadow: 0 0 0 5px rgba(23,23,23,.05);
          }}
          .title {{
            font-size: 17px;
            font-weight: 850;
            margin-bottom: 5px;
          }}
          .hint {{
            margin-top: 14px;
            color: #675f55;
            font-size: 12px;
          }}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="eyebrow">Color logic</div>
          <h2>Color carries meaning.</h2>
          <p id="summary">Click a color strip to inspect how the interface uses it.</p>
          <div class="strip" id="strip"></div>
          <div class="meaning">
            <span class="dot" id="dot"></span>
            <div>
              <div class="eyebrow">Selected color logic</div>
              <div class="title" id="title"></div>
              <p id="body"></p>
            </div>
          </div>
          <div class="hint">The selected strip changes this explanation in-place.</div>
        </div>
        <script>
          const data = {payload};
          const strip = document.getElementById("strip");
          const dot = document.getElementById("dot");
          const title = document.getElementById("title");
          const body = document.getElementById("body");
          const buttons = {{}};

          function selectColor(name) {{
            const item = data[name];
            dot.style.background = item.css;
            title.textContent = item.title;
            body.textContent = item.body;
            Object.entries(buttons).forEach(([buttonName, button]) => {{
              button.setAttribute("aria-pressed", String(buttonName === name));
            }});
          }}

          Object.entries(data).forEach(([name, item]) => {{
            const button = document.createElement("button");
            button.type = "button";
            button.title = name + ": " + item.title;
            button.setAttribute("aria-label", name + " color meaning");
            button.style.background = item.css;
            button.style.color = item.css;
            button.addEventListener("click", () => selectColor(name));
            buttons[name] = button;
            strip.appendChild(button);
          }});
          selectColor("Blue");
        </script>
      </body>
    </html>
    """


def shell_nav(section: str) -> None:
    st.markdown(
        f"""
        <div class="lab-shell-nav">
          <div class="lab-brand">Adaptive Equity Trading Lab</div>
          <div class="lab-nav-state">Current section: {section}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main_navigation(current_section: str) -> str:
    st.markdown(
        """
        <div class="main-nav-card">
          <div class="nav-help">Primary navigation stays usable even if the sidebar is closed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected = current_section if current_section in SECTIONS else SECTIONS[0]
    columns = st.columns([1] * len(SECTIONS))
    for column, section_name in zip(columns, SECTIONS):
        with column:
            button_type = "primary" if section_name == selected else "secondary"
            st.button(section_name, type=button_type, width="stretch", key=f"main_nav_{section_name}", on_click=set_active_section, args=(section_name,))
    return st.session_state.get("active_section", selected)


def set_active_section(section_name: str) -> None:
    st.session_state["active_section"] = section_name


@st.cache_data(show_spinner=False)
def cached_strategy_factory_components(factory_variant_limit: int) -> list[dict[str, object]]:
    return build_strategy_factory_components(max_variants=factory_variant_limit)


@st.cache_data(show_spinner=False)
def cached_factory_data_eligibility_report() -> dict[str, object]:
    return build_factory_data_eligibility_report()


def metric_card(label: str, value: str | int | float, note: str) -> None:
    value_text = str(value)
    value_class = "metric-value metric-value-long" if len(value_text) > 14 else "metric-value"
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="{value_class}">{value_text}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_guide(title: str, copy: str, cards: list[tuple[str, str, str]]) -> None:
    card_html = "".join(
        f"""
        <div class="guide-card {tone}">
          <div class="guide-title">{card_title}</div>
          <div class="guide-copy">{card_copy}</div>
        </div>
        """
        for card_title, card_copy, tone in cards
    )
    st.markdown(
        f"""
        <div class="page-guide">
          <div class="page-guide-title">{title}</div>
          <div class="page-guide-copy">{copy}</div>
          <div class="guide-grid">{card_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_note(text: str) -> None:
    st.markdown(f'<div class="section-note">{text}</div>', unsafe_allow_html=True)


def router_cell_class(posture: object) -> str:
    normalized = str(posture or "").upper()
    if "BLOCK" in normalized:
        return "block"
    if "REDUCE" in normalized:
        return "reduce"
    if "OVERLAY" in normalized:
        return "overlay"
    if "OBSERVE" in normalized:
        return "observe"
    if "ALLOW" in normalized or "PROXY" in normalized:
        return "proxy"
    return "proxy"


def humanize_router_label(value: object) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def render_router_matrix(router_matrix: pd.DataFrame) -> None:
    regimes = [str(regime) for regime in router_matrix["regime_label"].drop_duplicates().tolist()]
    families = [str(family) for family in router_matrix["strategy_family"].drop_duplicates().tolist()]
    lookup = {
        (str(row["strategy_family"]), str(row["regime_label"])): row
        for _, row in router_matrix.iterrows()
    }
    cells: list[str] = ['<div class="router-corner">Strategy family</div>']
    cells.extend(f'<div class="router-header">{escape(humanize_router_label(regime))}</div>' for regime in regimes)
    for family in families:
        cells.append(f'<div class="router-family">{escape(family)}</div>')
        for regime in regimes:
            row = lookup.get((family, regime))
            if row is None:
                posture = "NO DATA"
                score = ""
                why = "No router row for this family/regime pair."
            else:
                posture = str(row.get("posture", "UNKNOWN"))
                score_value = row.get("score", "")
                try:
                    score_number = float(score_value)
                except (TypeError, ValueError):
                    score = ""
                else:
                    score = f"score {score_number:.2f}" if not math.isnan(score_number) else ""
                why = str(row.get("why", ""))
            class_name = router_cell_class(posture)
            cells.append(
                f'<div class="router-cell {class_name}" title="{escape(why)}">'
                f"<strong>{escape(humanize_router_label(posture))}</strong><small>{escape(score)}</small></div>"
            )
    st.markdown(
        f"""
        <div class="router-matrix-shell">
          <div class="router-matrix" style="--regime-count: {max(len(regimes), 1)};">
            {''.join(cells)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_component_label(component_id: str, name: str, template: str | None = None) -> str:
    clean_name = str(name or component_id).replace("Factory ", "").replace("Materialized ", "")
    clean_name = " ".join(clean_name.split())
    short_id = f"F-{component_id.removeprefix('FACTORY-')[:6]}" if component_id.startswith("FACTORY-") else component_id[:6]
    if template:
        return f"{clean_name} | {template} | {short_id}"
    return f"{clean_name} | {short_id}"


def flow_chart(nodes: list[str]) -> go.Figure:
    if len(nodes) < 2:
        nodes = nodes + ["Decision"]
    x = [i / max(len(nodes) - 1, 1) for i in range(len(nodes))]
    y = [0.5 + (0.08 * math.sin(i)) for i in range(len(nodes))]
    fig = go.Figure()
    for i in range(len(nodes) - 1):
        fig.add_trace(
            go.Scatter(
                x=[x[i], x[i + 1]],
                y=[y[i], y[i + 1]],
                mode="lines",
                line=dict(color="#94a3b8", width=3),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    colors = ["#1f5eff"] + ["#0f9f75"] * max(len(nodes) - 2, 0) + ["#d97706"]
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers+text",
            marker=dict(size=30, color=colors[: len(nodes)], line=dict(color="#ffffff", width=2)),
            text=[f"{i + 1}" for i in range(len(nodes))],
            textfont=dict(color="white", size=12, family="IBM Plex Mono"),
            hovertext=nodes,
            hoverinfo="text",
            showlegend=False,
        )
    )
    for i, node in enumerate(nodes):
        fig.add_annotation(
            x=x[i],
            y=y[i] - 0.16,
            text=node,
            showarrow=False,
            font=dict(size=11, color="#171717", family="Instrument Sans"),
            align="center",
            width=130,
        )
    fig.update_layout(
        template="plotly_white",
        height=260,
        margin=dict(l=20, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[-0.04, 1.04]),
        yaxis=dict(visible=False, range=[0.15, 0.75]),
    )
    return fig


def strategy_result_chart(runs: pd.DataFrame) -> go.Figure:
    if runs.empty:
        frame = pd.DataFrame({"decision": ["not run"], "count": [1]})
    else:
        frame = runs.assign(decision=runs["decision"].astype(str).str.slice(0, 42)).groupby("decision", as_index=False).size()
        frame = frame.rename(columns={"size": "count"})
    fig = px.bar(
        frame,
        x="count",
        y="decision",
        orientation="h",
        color="count",
        color_continuous_scale=["#eef3ff", "#1f5eff"],
        text="count",
    )
    fig.update_layout(
        template="plotly_white",
        height=max(220, 52 * len(frame)),
        margin=dict(l=10, r=20, t=20, b=10),
        paper_bgcolor="rgba(255,255,255,.72)",
        plot_bgcolor="rgba(255,255,255,.72)",
        coloraxis_showscale=False,
        xaxis_title="Runs",
        yaxis_title="",
        font=dict(family="Instrument Sans", color="#171717"),
        xaxis=dict(tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
        yaxis=dict(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
    )
    return fig


def strategy_candlestick_chart(story: dict[str, object]) -> go.Figure:
    prices = story["prices"]
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        fig = go.Figure()
        fig.add_annotation(text="No local OHLCV panel available", x=0.5, y=0.5, showarrow=False)
        return fig
    markers = story.get("markers", [])
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=prices["date"],
            open=prices["open"],
            high=prices["high"],
            low=prices["low"],
            close=prices["close"],
            name="OHLC",
            increasing_line_color="#0f9f75",
            decreasing_line_color="#d97706",
            increasing_fillcolor="rgba(15,159,117,.65)",
            decreasing_fillcolor="rgba(217,119,6,.65)",
        )
    )
    volume_scale = float(prices["volume"].max()) if "volume" in prices and prices["volume"].max() else 1.0
    low = float(prices["low"].min())
    high = float(prices["high"].max())
    volume_height = (high - low) * 0.18 if high > low else 1.0
    fig.add_trace(
        go.Bar(
            x=prices["date"],
            y=(prices["volume"] / volume_scale * volume_height) + low,
            base=low,
            name="Volume pulse",
            marker=dict(color="rgba(31,94,255,.18)"),
            hovertemplate="Volume %{customdata:,}<extra></extra>",
            customdata=prices["volume"],
        )
    )
    marker_colors = {"buy": "#1f5eff", "entry": "#1f5eff", "exit": "#d97706", "block": "#d12f5f"}
    marker_symbols = {"buy": "triangle-up", "entry": "triangle-up", "exit": "circle", "block": "x"}
    for marker in markers:
        color = marker_colors.get(str(marker["kind"]), "#f97316")
        symbol = marker_symbols.get(str(marker["kind"]), "diamond")
        fig.add_trace(
            go.Scatter(
                x=[marker["date"]],
                y=[marker["price"]],
                mode="markers+text",
                marker=dict(size=14, color=color, symbol=symbol, line=dict(color="#ffffff", width=1.5)),
                text=[marker["label"]],
                textposition="top center",
                textfont=dict(size=11, color=color, family="IBM Plex Mono"),
                name=str(marker["label"]),
                hovertemplate="%{text}<br>%{x}<br>$%{y:.2f}<extra></extra>",
            )
        )
    risk_box = story.get("risk_box", {})
    if isinstance(risk_box, dict):
        for line_name, color, dash in [("stop_price", "#d12f5f", "dash"), ("take_profit_price", "#0f9f75", "dot")]:
            if line_name in risk_box:
                fig.add_hline(
                    y=float(risk_box[line_name]),
                    line=dict(color=color, width=2, dash=dash),
                    annotation_text=line_name.replace("_", " ").title(),
                    annotation_position="right",
                )
    fig.update_layout(
        template="plotly_white",
        title=dict(text=str(story["title"]), font=dict(size=16, family="Instrument Sans", color="#171717")),
        height=430,
        margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.78)",
        font=dict(family="Instrument Sans", color="#171717"),
        xaxis=dict(rangeslider=dict(visible=False), showgrid=True, gridcolor="#e7e2d8"),
        yaxis=dict(title="", showgrid=True, gridcolor="#e7e2d8", tickfont=dict(color="#3f3f46")),
        showlegend=False,
    )
    return fig


def render_hero(metrics: dict[str, object]) -> None:
    st.markdown(
        f"""
        <div class="lab-hero">
          <div class="lab-kicker">Final Research Console / Risk Regime Engine</div>
          <div class="lab-title">A quant lab that turned failed alpha into a risk machine.</div>
          <div class="lab-subtitle">
            Every strategy below has a real chart demonstration, a thesis, a governance path, and a final verdict.
            The current state is <strong>{metrics["final_policy"]}</strong>: no live deployment, no hidden promotion,
            and no strategy allowed past the cost and robustness gates.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(payload: dict[str, object]) -> None:
    metrics = governance_metrics(payload)
    render_hero(metrics)
    page_guide(
        "What this console is",
        "The dashboard is an audit surface for a research lab. Its job is not to sell a strategy; its job is to show what survived, what failed, and why the current mode is risk/regime research only.",
        [
            ("Ledger", "Every important conclusion is backed by a final decision artifact.", "data"),
            ("Gates", "Provider access, data quality, costs, and robustness decide what can continue.", "warn"),
            ("Zero promotion", "A strategy can look interesting and still remain locked.", "block"),
            ("Next layer", "Workbench and Portfolio Lab turn ideas into governed contracts.", "good"),
        ],
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Decisions", metrics["decision_count"], "Final decision files in the ledger")
    with c2:
        metric_card("Promoted", metrics["promoted_strategy_count"], "Strategies allowed through promotion gates")
    with c3:
        metric_card("Provider Queries", metrics["provider_query_rows"], "Rows that touched external providers")
    with c4:
        metric_card("Final Mode", metrics["final_policy"], "Research posture after closure")

    phase = payload["phase_summary"]
    blockers = phase.get("primary_blockers", [])
    st.markdown(
        f"""
        <div class="callout danger-callout">
          <strong>Operating conclusion:</strong> small-cap/free-data directional alpha is paused.
          The lab remains valuable as a risk-regime engine, data-quality gate, and falsification platform.
          Primary blockers: {", ".join(blockers) if blockers else "none recorded"}.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_strategy_tiles(payload)


def render_mission_brief(payload: dict[str, object]) -> None:
    metrics = governance_metrics(payload)
    status = build_mission_status({**payload, "metrics": metrics})
    st.markdown(
        """
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


def render_strategy_tiles(payload: dict[str, object]) -> None:
    rows = strategy_rows(payload["ledger"])
    st.subheader("Research Map")
    st.markdown('<div class="compact-grid">', unsafe_allow_html=True)
    for row in rows.to_dict("records"):
        st.markdown(
            f"""
            <div class="mini-tile">
              <div class="eyebrow">{row["family"]}</div>
              <div style="font-family:Instrument Sans,system-ui,sans-serif;font-weight:800;font-size:18px;margin:6px 0;">{row["name"]}</div>
              {status_badge(str(row["status"]))}
              <div class="small-muted" style="margin-top:8px;">{row["primary_decision"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_strategy_atlas(payload: dict[str, object]) -> None:
    ledger = payload["ledger"]
    rows = strategy_rows(ledger)
    st.header("Strategy Atlas")
    page_guide(
        "How to read the strategy atlas",
        "Each strategy gets the same treatment: what it tried to do, where it acted on a chart, why it failed or blocked, and what evidence remains useful.",
        [
            ("Chart first", "The candlestick panel shows the idea as a visual contract, not a backtest claim.", "data"),
            ("Explanation", "Plain language tells you what the rule was supposed to capture.", "good"),
            ("Verdict", "The result chart shows archive, block, diagnostic, or promotion state.", "warn"),
            ("Audit", "Raw run rows stay collapsed unless you need the ledger trail.", "block"),
        ],
    )

    left, right = st.columns([1, 2])
    status_counts = rows.groupby("status", as_index=False).size().rename(columns={"size": "count"})
    with left:
        status_fig = px.pie(
            status_counts,
            names="status",
            values="count",
            hole=0.58,
            color="status",
            color_discrete_map={
                "ARCHIVED": "#d97706",
                "BLOCKED": "#d12f5f",
                "DIAGNOSTIC": "#1f5eff",
                "NOT RUN": "#71717a",
                "PROMOTED": "#0f9f75",
            },
        )
        status_fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), font=dict(family="Instrument Sans", color="#171717"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(status_fig, width="stretch")
    with right:
        st.markdown(
            """
            <div class="callout">
            The charts are not meant to imply promotion. They explain how each strategy would see a stock chart:
            where a candidate signal appears, where the lab would enter or observe, and where the governance gate killed or blocked the idea.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(rows[["name", "family", "runs", "status"]], width="stretch", hide_index=True)

    for profile in STRATEGY_PROFILES:
        detail = strategy_detail(profile.key, ledger)
        runs = detail["runs"]
        story = build_strategy_chart_story(profile.key)
        st.markdown("---")
        header_l, header_r = st.columns([3, 1])
        with header_l:
            st.markdown(f'<div class="strategy-family">{profile.family}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="strategy-title">{profile.name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="strategy-copy">{profile.thesis}</div>', unsafe_allow_html=True)
        with header_r:
            st.markdown(status_badge(str(detail["status"])), unsafe_allow_html=True)

        chart_col, copy_col = st.columns([1.45, 1])
        with chart_col:
            st.plotly_chart(strategy_candlestick_chart(story), width="stretch")
        with copy_col:
            st.markdown("**How the strategy works**")
            st.write(profile.mechanism)
            st.markdown("**What the chart is showing**")
            st.write(story["explanation"])
            st.plotly_chart(strategy_result_chart(runs), width="stretch")

        st.markdown("**Decision graph**")
        st.plotly_chart(flow_chart(detail["flow_nodes"]), width="stretch")
        with st.expander("Open audit trail and raw run rows"):
            if runs.empty:
                st.info("No matching ledger rows for this strategy family.")
            else:
                wanted = ["run_id", "decision", "provider_query_performed", "market_data_download_performed", "backtest_performed", "promotion_allowed"]
                existing = [column for column in wanted if column in runs.columns]
                st.dataframe(runs[existing], width="stretch", hide_index=True)


def render_results_and_data(payload: dict[str, object], *, show_guide: bool = True) -> None:
    st.header("Results And Data Dashboard")
    if show_guide:
        page_guide(
            "How to read the data room",
            "This page separates evidence from raw artifact storage. Start with readiness and regime routing, then open the raw ledgers only when you need the audit trail.",
            [
                ("Readiness", "Which data paths can support real research and which remain blocked.", "data"),
                ("Regimes", "How the lab classifies market states and routes strategy families.", "good"),
                ("Diagnostics", "ORB, delisted gates, portfolio, and microstructure checks.", "warn"),
                ("Raw tables", "Full ledgers stay available but collapsed at the bottom.", "block"),
            ],
        )
    ledger = payload["ledger"]
    regime_map = payload["regime_map"]
    allocation = payload["allocation"]
    smallcap = payload["smallcap_microstructure"]
    data_matrix = payload["data_matrix"]
    orb = payload.get("orb_930", {})
    data_readiness = payload.get("data_readiness", {})
    strategy_router = payload.get("strategy_regime_router", {})

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Ledger Rows", len(ledger), "Final decisions and probes")
    with c2:
        metric_card("Regime Rows", len(regime_map), "Large-cap/ETF symbol-days mapped")
    with c3:
        metric_card("Data Upgrades", len(data_matrix), "Provider paths scored")

    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    if isinstance(data_readiness, dict):
        st.subheader("Data Readiness")
        st.markdown(
            """
            <div class="callout danger-callout">
            The free-provider mesh is not admissible for a true survivorship-free backtest yet. The lab can inspect
            components, but Candidate 012 remains blocked until one data bundle covers PIT universe membership,
            delisted terminal prices, adjusted OHLCV, corporate actions, and benchmarks together.
            </div>
            """,
            unsafe_allow_html=True,
        )
        r1, r2, r3 = st.columns(3)
        readiness_table = data_readiness.get("table", pd.DataFrame())
        with r1:
            metric_card("Data mesh", data_readiness.get("status", "UNKNOWN"), "Current data-readiness decision")
        with r2:
            metric_card("Backtest allowed", "NO" if not data_readiness.get("candidate_012_backtest_allowed") else "YES", "Candidate 012 true backtest")
        with r3:
            metric_card("Providers checked", len(readiness_table) if isinstance(readiness_table, pd.DataFrame) else 0, "Component probes and audits")
        if isinstance(readiness_table, pd.DataFrame) and not readiness_table.empty:
            plot_rows = readiness_table.copy()
            fig = px.bar(
                plot_rows,
                x="coverage_score",
                y="provider",
                orientation="h",
                color="admissibility",
                color_discrete_map={
                    "component_pass": "#0f9f75",
                    "partial_not_admissible": "#d97706",
                    "blocked_history_depth": "#7c3aed",
                    "blocked_reference_entitlement": "#7c3aed",
                    "not_admissible": "#d12f5f",
                },
                hover_data=["decision", "hard_blocks", "role"],
            )
            fig.update_layout(
                template="plotly_white",
                height=360,
                margin=dict(l=0, r=10, t=10, b=10),
                xaxis_title="Coverage score (not a pass score)",
                yaxis_title="",
                paper_bgcolor="rgba(255,255,255,.72)",
                plot_bgcolor="rgba(255,255,255,.72)",
                font=dict(color="#171717", family="Instrument Sans"),
                legend_title_text="Evidence status",
            )
            fig.update_xaxes(range=[0, 1], tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            st.plotly_chart(fig, width="stretch")
            visible_cols = [
                "provider",
                "role",
                "decision",
                "active_ohlcv",
                "corporate_actions",
                "identity_continuity",
                "delisted_terminal",
                "benchmarks",
                "pit_universe",
                "next_action",
            ]
            with st.expander("Audit details: provider readiness rows"):
                st.dataframe(readiness_table[visible_cols], width="stretch", hide_index=True)
        next_paths = data_readiness.get("next_best_paths", [])
        if next_paths:
            st.markdown("**What this means operationally**")
            for item in next_paths:
                st.markdown(f"- {item}")

    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    if isinstance(strategy_router, dict):
        router_matrix = strategy_router.get("matrix", pd.DataFrame())
        router_summary = strategy_router.get("summary", pd.DataFrame())
        st.subheader("Strategy x Market Regime Router")
        st.markdown(
            f"""
            <div class="callout amber-callout">
            {strategy_router.get("interpretation", "Diagnostic-only regime router.")}
            No provider query, no market-data download, no backtest, and no promotion are performed here.
            </div>
            """,
            unsafe_allow_html=True,
        )
        q1, q2, q3 = st.columns(3)
        with q1:
            metric_card("Router status", strategy_router.get("status", "UNKNOWN"), "Risk map, not alpha")
        with q2:
            metric_card("Families", strategy_router.get("families_mapped", 0), "Strategy families routed")
        with q3:
            metric_card("Regimes", strategy_router.get("regimes_mapped", 0), "Market states mapped")

        if isinstance(router_matrix, pd.DataFrame) and not router_matrix.empty:
            posture_text = router_matrix.pivot(index="strategy_family", columns="regime_label", values="posture")
            score_matrix = router_matrix.pivot(index="strategy_family", columns="regime_label", values="score")
            hover_matrix = router_matrix.pivot(index="strategy_family", columns="regime_label", values="why")
            fig = go.Figure(
                data=go.Heatmap(
                    z=score_matrix.to_numpy(),
                    x=list(score_matrix.columns),
                    y=list(score_matrix.index),
                    text=posture_text.to_numpy(),
                    customdata=hover_matrix.to_numpy(),
                    texttemplate="%{text}",
                    hovertemplate="<b>%{y}</b><br>%{x}<br>Posture: %{text}<br>%{customdata}<extra></extra>",
                    colorscale=[
                        [0.00, "#d12f5f"],
                        [0.35, "#d97706"],
                        [0.60, "#1f5eff"],
                        [1.00, "#0f9f75"],
                    ],
                    zmin=0,
                    zmax=1,
                    showscale=False,
                )
            )
            fig.update_layout(
                height=440,
                margin=dict(l=0, r=0, t=10, b=10),
                xaxis_title="Market regime",
                yaxis_title="Strategy family",
                paper_bgcolor="rgba(255,255,255,.72)",
                plot_bgcolor="rgba(255,255,255,.72)",
                font=dict(color="#171717", family="Instrument Sans"),
            )
            fig.update_xaxes(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            st.plotly_chart(fig, width="stretch")
            st.caption("Reading rule: red blocks capital, amber reduces sizing, blue is proxy-only exploration, green is risk overlay/governance.")

            if isinstance(router_summary, pd.DataFrame) and not router_summary.empty:
                st.markdown("**Operational routing notes**")
                st.dataframe(
                    router_summary[["strategy_family", "best_regime", "best_posture", "blocked_regimes", "operating_rule"]],
                    width="stretch",
                    hide_index=True,
                )
            with st.expander("Open full regime-strategy contract"):
                st.dataframe(
                    router_matrix[
                        [
                            "strategy_family",
                            "strategies",
                            "regime_label",
                            "posture",
                            "score",
                            "why",
                            "main_failure_mode",
                            "allowed_use",
                        ]
                    ],
                    width="stretch",
                    hide_index=True,
                )

    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    if isinstance(orb, dict) and orb.get("available"):
        decision = orb.get("decision", {})
        best = orb.get("best", {})
        summary = orb.get("summary", pd.DataFrame())
        by_symbol = orb.get("by_symbol", pd.DataFrame())
        st.subheader("9:30 AM Opening Range Breakout")
        st.markdown(
            """
            <div class="callout amber-callout">
            This is the requested cross-asset ORB test: first 5m/15m New York range, entry only before 11:00,
            stop on the opposite side of the range, 1R/3R/4R targets, session exit at 16:00. It is a completed
            exploratory backtest, not a promoted strategy.
            </div>
            """,
            unsafe_allow_html=True,
        )
        o1, o2, o3, o4 = st.columns(4)
        with o1:
            metric_card("Decision", decision.get("decision", "UNKNOWN"), "Final ORB verdict")
        with o2:
            metric_card("Total trades", decision.get("trade_count_total", 0), "All symbols and parameter rows")
        with o3:
            metric_card("Best config", f"{best.get('symbol', 'n/a')} {best.get('range_minutes', 'n/a')}m/{best.get('reward_r', 'n/a')}R", "By net return sum")
        with o4:
            metric_card("Median net", best.get("median_net_return", "n/a"), "Typical trade after cost")
        orb_cols = st.columns([1.2, 1])
        with orb_cols[0]:
            if isinstance(summary, pd.DataFrame) and not summary.empty:
                top_summary = summary.sort_values("net_return_sum", ascending=False).head(9)
                fig = px.bar(
                    top_summary,
                    x="net_return_sum",
                    y=top_summary.apply(lambda row: f"{row['symbol']} {int(row['range_minutes'])}m/{int(row['reward_r'])}R", axis=1),
                    orientation="h",
                    color="median_net_return",
                    color_continuous_scale=["#d12f5f", "#d97706", "#0f9f75"],
                    hover_data=["trades", "win_rate", "average_net_return"],
                )
                fig.update_layout(
                    template="plotly_white",
                    height=360,
                    margin=dict(l=0, r=0, t=20, b=10),
                    xaxis_title="Net return sum",
                    yaxis_title="Configuration",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#171717", family="Instrument Sans"),
                )
                fig.update_xaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                fig.update_coloraxes(colorbar_tickfont=dict(color="#171717"), colorbar_title_font=dict(color="#171717"))
                st.plotly_chart(fig, width="stretch")
        with orb_cols[1]:
            if isinstance(by_symbol, pd.DataFrame) and not by_symbol.empty:
                fig = px.pie(by_symbol, names="symbol", values="trades", hole=0.55, color_discrete_sequence=["#1f5eff", "#0f9f75", "#d97706"])
                fig.update_layout(
                    height=360,
                    margin=dict(l=0, r=0, t=20, b=10),
                    font=dict(color="#171717", family="Instrument Sans"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, width="stretch")
        with st.expander("Open ORB parameter table and report"):
            if isinstance(summary, pd.DataFrame) and not summary.empty:
                st.dataframe(summary.sort_values("net_return_sum", ascending=False), width="stretch", hide_index=True)
            report_text = str(orb.get("report_text", ""))
            if report_text:
                st.markdown(report_text)

    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    delisted_gate = delisted_data_source_gate_payload()
    st.subheader("Delisted Data Source Gate")
    st.markdown(
        """
        <div class="callout danger-callout">
        PDUFA Investment Mode remains <strong>PROXY_INVESTMENT_CANDIDATE_ONLY</strong> until a survivor-bias-free source supplies
        delisted common-stock prices, listing/delisting dates, corporate actions, PIT membership, and a separate PIT PDUFA/FDA calendar.
        This gate performs no provider query and no backtest.
        </div>
        """,
        unsafe_allow_html=True,
    )
    g1, g2, g3 = st.columns(3)
    with g1:
        metric_card("Gate status", delisted_gate["manifest"].get("status", "missing"), "Source contract only")
    with g2:
        metric_card("Admissible sources", len(delisted_gate["admissible_sources"]), ", ".join(delisted_gate["admissible_sources"]) or "none")
    with g3:
        metric_card("Candidate status", delisted_gate["manifest"].get("current_candidate_status", "unknown"), "No capital deployment")
    matrix = delisted_gate["candidate_source_matrix"]
    requirements = delisted_gate["unlock_requirements"]
    with st.expander("Audit details: delisted source matrix and unlock requirements"):
        gate_cols = st.columns([1.25, 1])
        with gate_cols[0]:
            if not matrix.empty:
                st.dataframe(
                    matrix[["provider", "delisted_symbols", "survivorship_free_prices", "pit_membership", "gate_status", "notes"]],
                    width="stretch",
                    hide_index=True,
                )
        with gate_cols[1]:
            if not requirements.empty:
                st.dataframe(requirements[["requirement_id", "failure_action"]], width="stretch", hide_index=True)
    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if not ledger.empty:
            counts = ledger.groupby("decision", as_index=False).size().sort_values("size", ascending=False).head(12)
            fig = px.bar(counts, x="size", y="decision", orientation="h", color="size", color_continuous_scale=["#eef3ff", "#1f5eff"])
            fig.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=0, r=10, t=10, b=10),
                coloraxis_showscale=False,
                yaxis_title="",
                xaxis_title="Count",
                paper_bgcolor="rgba(255,255,255,.72)",
                plot_bgcolor="rgba(255,255,255,.72)",
                font=dict(color="#171717", family="Instrument Sans"),
                xaxis=dict(tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
                yaxis=dict(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
            )
            st.plotly_chart(fig, width="stretch")
    with c2:
        if not regime_map.empty and "regime_label" in regime_map.columns:
            regime_counts = regime_map.groupby("regime_label", as_index=False).size()
            fig = px.bar(regime_counts, x="regime_label", y="size", color="regime_label", color_discrete_sequence=["#1f5eff", "#0f9f75", "#d97706", "#7c3aed", "#d12f5f", "#71717a"])
            fig.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=0, r=0, t=10, b=10),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Symbol-days",
                paper_bgcolor="rgba(255,255,255,.72)",
                plot_bgcolor="rgba(255,255,255,.72)",
                font=dict(color="#171717", family="Instrument Sans"),
                xaxis=dict(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
                yaxis=dict(tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8"),
            )
            st.plotly_chart(fig, width="stretch")

    st.subheader("Portfolio And Microstructure Diagnostics")
    m1, m2 = st.columns(2)
    with m1:
        if not allocation.empty and {"symbol", "diagnostic_weight"}.issubset(allocation.columns):
            fig = px.bar(
                allocation.sort_values("diagnostic_weight", ascending=False),
                x="symbol",
                y="diagnostic_weight",
                color="realized_volatility",
                color_continuous_scale="Blues",
            )
            fig.update_layout(template="plotly_white", height=340, margin=dict(l=0, r=0, t=10, b=10), xaxis_title="", yaxis_title="Diagnostic weight")
            st.plotly_chart(fig, width="stretch")
    with m2:
        if not smallcap.empty and {"symbol", "median_dollar_volume", "median_spread_proxy"}.issubset(smallcap.columns):
            fig = px.scatter(
                smallcap,
                x="median_dollar_volume",
                y="median_spread_proxy",
                size="observations",
                color="symbol",
                hover_name="symbol",
                log_x=True,
            )
            fig.update_layout(template="plotly_white", height=340, margin=dict(l=0, r=0, t=10, b=10), xaxis_title="Median dollar volume", yaxis_title="Spread proxy")
            st.plotly_chart(fig, width="stretch")

    st.subheader("Data Upgrade Matrix")
    if not data_matrix.empty:
        st.caption("Provider capability rows are audit material: open them when you need to inspect the data contract.")
        with st.expander("Audit details: provider data upgrade matrix"):
            st.dataframe(data_matrix, width="stretch", hide_index=True)

    with st.expander("Open raw decision ledger"):
        st.dataframe(ledger, width="stretch", hide_index=True)
    with st.expander("Open raw regime map"):
        st.dataframe(regime_map, width="stretch", hide_index=True)
    with st.expander("Open raw allocation and microstructure tables"):
        st.dataframe(allocation, width="stretch", hide_index=True)
        st.dataframe(smallcap, width="stretch", hide_index=True)


def render_lab_explainer(payload: dict[str, object]) -> None:
    st.header("Project Anatomy")
    st.markdown(
        """
        <div class="callout">
        The project is not a simple backtester. It is a falsification machine: every idea must pass data quality,
        timestamp integrity, cost realism, sample-size, robustness, and governance gates before it can become a candidate.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("The Life Of The Project")
    st.write(
        "This section tells the research arc, not just the final architecture: where the ideas came from, "
        "what the lab tried to prove, why each branch was stopped, and what survived as reusable infrastructure."
    )
    lifecycle = project_lifecycle_rows()
    for index, row in enumerate(lifecycle.to_dict("records")):
        if index % 2 == 0:
            cols = st.columns(2)
        with cols[index % 2]:
            st.markdown(
                f"""
                <div class="lifecycle-card">
                  <div class="lifecycle-source">{row["idea_source"]}</div>
                  <div class="lifecycle-phase">{row["phase"]}</div>
                  <div class="strategy-copy"><strong>What happened:</strong> {row["what_happened"]}</div>
                  <div class="strategy-copy" style="margin-top:10px;"><strong>Why it matters:</strong> {row["lesson"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)

    st.subheader("Lab Pipeline")
    nodes = [
        "Hypothesis",
        "Pre-run gate",
        "Data contract",
        "Backtest / diagnostic",
        "Cost realism",
        "Robustness",
        "Final decision",
        "Archive or block",
    ]
    st.plotly_chart(flow_chart(nodes), width="stretch")

    st.subheader("Capabilities Built Along The Way")
    capabilities = project_capability_rows()
    st.markdown('<div class="capability-grid">', unsafe_allow_html=True)
    for row in capabilities.to_dict("records"):
        st.markdown(
            f"""
            <div class="capability">
              <div class="strategy-family">{row["area"]} / {row["state"]}</div>
              <div style="font-family:Exo,system-ui,sans-serif;font-weight:800;margin:8px 0;">{row["capability"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    rules = payload["operating_rules"]
    st.subheader("Operating Rules")
    st.write("The lab separates allowed research actions from forbidden trading or promotion actions.")
    with st.expander("Audit details: allowed and forbidden action rules"):
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**Allowed**")
            st.json(rules.get("allowed_actions", {}))
        with r2:
            st.markdown("**Forbidden**")
            st.json(rules.get("forbidden_actions", {}))

    st.subheader("Next Product Layer")
    st.write(
        "The next phase can become a user-facing strategy workbench: users define rules, choose data assumptions, run the same governance gates, "
        "and inspect results without bypassing PIT, cost, robustness, or promotion controls. This dashboard intentionally stops before that builder."
    )


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


def render_regime_playbook_panel(payload: dict[str, object]) -> None:
    regime_map = payload["regime_map"]
    strategy_router = payload.get("strategy_regime_router", {})
    router_matrix = strategy_router.get("matrix", pd.DataFrame()) if isinstance(strategy_router, dict) else pd.DataFrame()
    router_summary = strategy_router.get("summary", pd.DataFrame()) if isinstance(strategy_router, dict) else pd.DataFrame()

    st.subheader("Market Regime Router")
    st.markdown(
        f"""
        <div class="callout amber-callout">
        {strategy_router.get("interpretation", "Diagnostic-only regime router.") if isinstance(strategy_router, dict) else "Diagnostic-only regime router."}
        This page answers one question only: which strategy families should be full-size, reduced, observe-only, or blocked in each market state.
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    with q1:
        metric_card("Router status", strategy_router.get("status", "UNKNOWN") if isinstance(strategy_router, dict) else "UNKNOWN", "Risk map, not alpha")
    with q2:
        metric_card("Families", strategy_router.get("families_mapped", 0) if isinstance(strategy_router, dict) else 0, "Strategy sleeves routed")
    with q3:
        metric_card("Regimes", strategy_router.get("regimes_mapped", 0) if isinstance(strategy_router, dict) else 0, "Market states mapped")

    if isinstance(router_matrix, pd.DataFrame) and not router_matrix.empty:
        render_router_matrix(router_matrix)
        st.caption("Reading rule: red blocks capital, amber reduces sizing, blue is proxy-only exploration, green is risk overlay/governance.")

    if isinstance(router_summary, pd.DataFrame) and not router_summary.empty:
        st.markdown("**Operational routing notes**")
        st.caption("This table is the playbook: one row per strategy family, best regime, failure mode, and operating rule.")
        st.dataframe(
            router_summary[["strategy_family", "best_regime", "best_posture", "blocked_regimes", "operating_rule"]],
            width="stretch",
            hide_index=True,
        )

    if isinstance(regime_map, pd.DataFrame) and not regime_map.empty and "regime_label" in regime_map.columns:
        st.markdown("**Observed local regime mix**")
        regime_counts = regime_map.groupby("regime_label", as_index=False).size()
        fig = px.bar(
            regime_counts,
            x="regime_label",
            y="size",
            color="regime_label",
            text="size",
            color_discrete_sequence=["#1f5eff", "#0f9f75", "#d97706", "#7c3aed", "#d12f5f", "#71717a"],
        )
        fig.update_traces(textposition="outside", textfont=dict(color="#0f172a", size=13, family="IBM Plex Mono"))
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=10, r=10, t=26, b=60),
            showlegend=False,
            xaxis_title="",
            yaxis_title="Symbol-days",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#171717", family="Instrument Sans"),
        )
        fig.update_xaxes(tickfont=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a"), gridcolor="#d5dbe5")
        fig.update_yaxes(tickfont=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a"), gridcolor="#d5dbe5")
        st.plotly_chart(fig, width="stretch")

    with st.expander("Audit details: full regime-strategy contract"):
        if isinstance(router_matrix, pd.DataFrame) and not router_matrix.empty:
            st.dataframe(
                router_matrix[
                    [
                        "strategy_family",
                        "strategies",
                        "regime_label",
                        "posture",
                        "score",
                        "why",
                        "main_failure_mode",
                        "allowed_use",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )
        if isinstance(regime_map, pd.DataFrame) and not regime_map.empty:
            st.dataframe(regime_map, width="stretch", hide_index=True)


def render_data_vault_panel(payload: dict[str, object]) -> None:
    data_readiness = payload.get("data_readiness", {})
    data_matrix = payload["data_matrix"]

    st.subheader("Admissible Data Gate")
    st.markdown(
        """
        <div class="callout danger-callout">
        This page is only about data admissibility. A strategy can look good in proxy mode and still remain locked
        until one bundle covers PIT membership, delisted symbols, adjusted OHLCV, corporate actions, and benchmarks.
        </div>
        """,
        unsafe_allow_html=True,
    )

    readiness_table = data_readiness.get("table", pd.DataFrame()) if isinstance(data_readiness, dict) else pd.DataFrame()
    r1, r2, r3 = st.columns(3)
    with r1:
        metric_card("Data mesh", data_readiness.get("status", "UNKNOWN") if isinstance(data_readiness, dict) else "UNKNOWN", "Current data-readiness decision")
    with r2:
        allowed = data_readiness.get("candidate_012_backtest_allowed") if isinstance(data_readiness, dict) else False
        metric_card("Backtest allowed", "YES" if allowed else "NO", "True-test gate")
    with r3:
        metric_card("Providers checked", len(readiness_table) if isinstance(readiness_table, pd.DataFrame) else 0, "Provider/component probes")

    if isinstance(readiness_table, pd.DataFrame) and not readiness_table.empty:
        fig = px.bar(
            readiness_table,
            x="coverage_score",
            y="provider",
            orientation="h",
            color="admissibility",
            color_discrete_map={
                "component_pass": "#0f9f75",
                "partial_not_admissible": "#d97706",
                "blocked_history_depth": "#7c3aed",
                "blocked_reference_entitlement": "#7c3aed",
                "not_admissible": "#d12f5f",
            },
            hover_data=["decision", "hard_blocks", "role"],
        )
        fig.update_layout(
            template="plotly_white",
            height=380,
            margin=dict(l=0, r=10, t=10, b=10),
            xaxis_title="Coverage score (not a pass score)",
            yaxis_title="",
            paper_bgcolor="rgba(255,255,255,.72)",
            plot_bgcolor="rgba(255,255,255,.72)",
            font=dict(color="#171717", family="Instrument Sans"),
            legend_title_text="Evidence status",
        )
        fig.update_xaxes(range=[0, 1], tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
        fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
        st.plotly_chart(fig, width="stretch")

        visible_cols = [
            "provider",
            "role",
            "decision",
            "active_ohlcv",
            "corporate_actions",
            "identity_continuity",
            "delisted_terminal",
            "benchmarks",
            "pit_universe",
            "next_action",
        ]
        with st.expander("Audit details: provider readiness rows"):
            st.dataframe(readiness_table[visible_cols], width="stretch", hide_index=True)

    next_paths = data_readiness.get("next_best_paths", []) if isinstance(data_readiness, dict) else []
    if next_paths:
        st.markdown("**Next admissible data paths**")
        for item in next_paths:
            st.markdown(f"- {item}")

    delisted_gate = delisted_data_source_gate_payload()
    st.subheader("Delisted Coverage Requirement")
    g1, g2, g3 = st.columns(3)
    with g1:
        metric_card("Gate status", delisted_gate["manifest"].get("status", "missing"), "Source contract only")
    with g2:
        metric_card("Admissible sources", len(delisted_gate["admissible_sources"]), ", ".join(delisted_gate["admissible_sources"]) or "none")
    with g3:
        metric_card("Candidate status", delisted_gate["manifest"].get("current_candidate_status", "unknown"), "No capital deployment")

    with st.expander("Audit details: delisted source matrix and unlock requirements"):
        gate_cols = st.columns([1.25, 1])
        matrix = delisted_gate["candidate_source_matrix"]
        requirements = delisted_gate["unlock_requirements"]
        with gate_cols[0]:
            if not matrix.empty:
                st.dataframe(
                    matrix[["provider", "delisted_symbols", "survivorship_free_prices", "pit_membership", "gate_status", "notes"]],
                    width="stretch",
                    hide_index=True,
                )
        with gate_cols[1]:
            if not requirements.empty:
                st.dataframe(requirements[["requirement_id", "failure_action"]], width="stretch", hide_index=True)

    st.subheader("Provider Upgrade Matrix")
    st.caption("This is the provider capability map, not a performance report.")
    with st.expander("Audit details: provider data upgrade matrix"):
        if not data_matrix.empty:
            st.dataframe(data_matrix, width="stretch", hide_index=True)


def render_decision_ledger_panel(payload: dict[str, object]) -> None:
    ledger = payload["ledger"]
    metrics = governance_metrics(payload)

    st.subheader("Final Decision Ledger")
    st.markdown(
        """
        <div class="callout">
        This page is the audit trail. It does not explain regimes or providers first; it answers what the lab decided,
        which runs touched external sources, and where the raw evidence lives.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Decisions", metrics["decision_count"], "Final decision artifacts")
    with c2:
        metric_card("Provider queries", metrics["provider_query_rows"], "Rows that touched providers")
    with c3:
        metric_card("Promoted", metrics["promoted_strategy_count"], "Promotion gates passed")
    with c4:
        metric_card("Final mode", metrics["final_policy"], "Current posture")

    if not ledger.empty:
        counts = ledger.groupby("decision", as_index=False).size().sort_values("size", ascending=False).head(14)
        fig = px.bar(counts, x="size", y="decision", orientation="h", color="size", text="size", color_continuous_scale=["#93c5fd", "#2563eb"])
        fig.update_traces(textposition="outside", textfont=dict(color="#0f172a", size=12, family="IBM Plex Mono"), cliponaxis=False)
        fig.update_layout(
            template="plotly_white",
            height=520,
            margin=dict(l=18, r=52, t=18, b=28),
            coloraxis_showscale=False,
            yaxis_title="",
            xaxis_title="Count",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#171717", family="Instrument Sans"),
        )
        fig.update_xaxes(tickfont=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a"), gridcolor="#d5dbe5")
        fig.update_yaxes(tickfont=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a"), gridcolor="#d5dbe5")
        st.plotly_chart(fig, width="stretch")

        if "provider_query_performed" in ledger.columns:
            provider_rows = ledger[ledger["provider_query_performed"].astype(str).str.lower().isin(["true", "1", "yes"])]
            st.markdown("**Provider-query rows**")
            st.caption("These rows are the ones that crossed from local artifact reading into external provider interaction.")
            if provider_rows.empty:
                st.info("No provider-query rows in the current ledger view.")
            else:
                visible = [column for column in ["run_id", "decision", "provider_query_performed", "market_data_download_performed", "backtest_performed", "promotion_allowed"] if column in provider_rows.columns]
                st.dataframe(provider_rows[visible], width="stretch", hide_index=True)

    with st.expander("Audit details: raw decision ledger"):
        st.dataframe(ledger, width="stretch", hide_index=True)


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
    render_regime_playbook_panel(payload)


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
    render_data_vault_panel(payload)


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
    render_decision_ledger_panel(payload)


def render_strategy_workbench() -> None:
    hero_left, hero_right = st.columns([1.35, 0.58], gap="large")
    with hero_left:
        st.markdown(
            """
          <div class="human-workbench-copy">
            <div class="lab-kicker">Human strategy workbench</div>
            <h1>Build the idea. Then let the lab disagree.</h1>
            <p>
              Define a strategy like a researcher, not like a gambler. The workbench translates your rule into a falsifiable contract,
              shows what data is actually available, and keeps promotion locked until the gates survive.
            </p>
          </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        st.iframe(color_logic_component_html(), height=330)

    page_guide(
        "How to read this page",
        "The Workbench is a drafting room. It does not prove alpha. It turns an idea into a governed local dry-run so the lab can explain, reject, or package it without hiding the assumptions.",
        [
            ("1. Draft", "Name the idea, choose its family, universe, holding period, and cost model.", "data"),
            ("2. Preview", "Read the strategy in plain English before any result is shown.", "good"),
            ("3. Gate", "The pre-run gate says whether the dry-run is allowed and what is still blocked.", "warn"),
            ("4. Inspect", "Charts, trade rows, robustness gates, and packages live after the verdict.", "block"),
        ],
    )

    st.markdown(
        f"""
        <div class="workbench-card" style="border-top:4px solid var(--lab-plum);">
          <div class="eyebrow">Template catalog</div>
          <div class="strategy-title" style="font-size:30px;">{len(WORKBENCH_TEMPLATES)} strategy families, not 4</div>
          <div class="strategy-copy">
            These are not promoted strategies. They are starting contracts for future tests: momentum, reversion,
            catalysts, PEAD, insider filings, dollar bars, risk regimes, biotech calendars, and activist filings.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">01 / Composer</div>
          <div class="workbench-section-title">Turn a trading idea into a contract.</div>
          <div class="workbench-section-copy">
            The left side captures your intent in frozen assumptions. The right side translates it into the first audit object the lab can validate.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.82, 1.18], gap="large")
    with left:
        st.subheader("Strategy Draft")
        idea_tab, data_tab, risk_tab, run_tab = st.tabs(["1 Idea", "2 Data", "3 Risk", "4 Run"])
        with idea_tab:
            st.markdown('<span class="workbench-step">1</span><strong>Name the hypothesis</strong>', unsafe_allow_html=True)
            st.caption("Use a name that can survive in the ledger, not a vague note like 'new idea'.")
            name = st.text_input("Strategy name", value="My falsifiable strategy")
            st.markdown('<span class="workbench-step">2</span><strong>Choose the strategy family</strong>', unsafe_allow_html=True)
            st.caption("The family defines the first data contract and the first blocker the lab will apply.")
            template = st.selectbox("Strategy template", list(WORKBENCH_TEMPLATES.keys()))
            selected_template = WORKBENCH_TEMPLATES[template]
            st.info(selected_template["signal"])
        custom_rules = None
        with data_tab:
            st.markdown('<span class="workbench-step">3</span><strong>Choose the universe</strong>', unsafe_allow_html=True)
            st.caption("This controls whether the result can ever be promotable or is only exploratory.")
            universe = st.selectbox(
                "Universe",
                [
                    "large-cap / ETF clean-data sandbox",
                    "small-cap active-only exploratory sandbox",
                    "expanded local research sandbox",
                    "local archived Databento panel",
                    "custom universe pending PIT validation",
                ],
            )
            if template == "Custom Rule Builder":
                st.markdown('<span class="workbench-step">3B</span><strong>Define the local rule</strong>', unsafe_allow_html=True)
                st.caption("These controls change the local dry-run rule. They still use only archived OHLCV, no provider query.")
                custom_signal = st.selectbox(
                    "Custom signal",
                    ["momentum_21d", "momentum_5d", "dip_2d", "low_vol_5d", "volume_shock", "dollar_volume_shock"],
                    help="The OHLCV feature used to rank entry windows.",
                )
                custom_selection = st.radio(
                    "Selection direction",
                    ["top", "bottom"],
                    horizontal=True,
                    help="Top buys the highest-ranked windows; bottom buys the lowest-ranked windows.",
                )
                custom_entries = st.slider("Entry windows per symbol", min_value=1, max_value=120, value=20)
                custom_filter = st.selectbox(
                    "Market filter",
                    ["none", "positive_5d", "negative_5d", "volume_above_20d", "low_volatility_20d"],
                    help="Adds a simple local OHLCV filter before ranking windows.",
                )
                custom_allowed = st.text_area(
                    "Optional allowed symbols",
                    value="",
                    placeholder="Example: CABA, CRMD, IOVA, SPY. Leave empty to use all locally routed symbols.",
                    help="This filters only the local dry-run universe. It does not download missing prices.",
                )
            else:
                custom_signal = "momentum_21d"
                custom_selection = "top"
                custom_entries = 20
                custom_filter = "none"
                custom_allowed = ""
        with risk_tab:
            st.markdown('<span class="workbench-step">4</span><strong>Set the test assumptions</strong>', unsafe_allow_html=True)
            st.caption("These numbers become part of the hypothesis. They cannot be tuned after seeing the result.")
            st.markdown("**Holding period**: how long the simulated position is allowed to stay open.")
            holding_period = st.slider("Holding period days", min_value=1, max_value=180, value=21)
            st.markdown("**Analysis mode**: trading mode judges each signal; investment mode judges the basket.")
            strategy_mode = st.selectbox("Analysis mode", ["Auto", "Trading", "Investment"])
            if strategy_mode == "Auto":
                inferred_mode = "Investment" if holding_period > 30 else "Trading"
                st.caption(f"Auto currently resolves to {inferred_mode} because holding period is {holding_period} days.")
            st.markdown("**Cost model**: round-trip execution friction. Small-cap tests should stay conservative.")
            cost_bps = st.slider("Round-trip cost model (bps)", min_value=0, max_value=1000, value=500, step=25)
            custom_exit = st.selectbox(
                "Exit policy",
                ["holding_period", "risk_box"],
                help="Holding period exits at the fixed horizon. Risk box can exit earlier on stop/take-profit touches.",
            )
            stop_loss_pct = st.slider("Stop loss %", min_value=1, max_value=80, value=15, disabled=custom_exit != "risk_box")
            take_profit_pct = st.slider("Take profit %", min_value=1, max_value=300, value=30, disabled=custom_exit != "risk_box")
        with run_tab:
            st.markdown("**Provider query**: external data must be explicitly allowed and gated before any call.")
            provider_query = st.checkbox("Allow external provider query after pre-run gate", value=False)
            st.caption("The dry-run button remains below the validation section so the gate is always visible first.")
        if template == "Custom Rule Builder":
            custom_rules = {
                "signal": custom_signal,
                "selection": custom_selection,
                "entries_per_symbol": custom_entries,
                "market_filter": custom_filter,
                "exit_policy": custom_exit,
                "stop_loss_pct": stop_loss_pct,
                "take_profit_pct": take_profit_pct,
                "allowed_symbols": custom_allowed,
            }
    with right:
        st.subheader("Readable Preview")
        manifest = build_workbench_manifest(
            name=name,
            template=template,
            universe=universe,
            holding_period_days=holding_period,
            cost_bps=cost_bps,
            allow_provider_query=provider_query,
            strategy_mode=strategy_mode,
            custom_rules=custom_rules,
        )
        st.markdown(
            f"""
            <div class="workbench-card" style="border-top:4px solid var(--lab-blue);">
              <div class="eyebrow">Strategy contract</div>
              <div class="strategy-title" style="font-size:28px;">{manifest["strategy_name"]}</div>
              <div class="strategy-copy"><strong>Template:</strong> {manifest["template"]}</div>
              <div class="strategy-copy"><strong>Universe:</strong> {manifest["universe"]}</div>
              <div class="strategy-copy"><strong>Analysis mode:</strong> {manifest["analysis_mode"]} <span class="small-muted">(requested: {manifest["requested_mode"]})</span></div>
              <div class="strategy-copy"><strong>First gate:</strong> {manifest["first_gate"]}</div>
              <div class="strategy-copy"><strong>Promotion:</strong> locked to <code>false</code> until validation passes.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        rule_cols = st.columns(2)
        with rule_cols[0]:
            st.markdown(
                f"""
                <div class="rule-card" style="border-top-color:var(--lab-blue);">
                  <div class="rule-title">Entry Rule</div>
                  <div class="small-muted">{manifest["entry_rule"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with rule_cols[1]:
            st.markdown(
                f"""
                <div class="rule-card" style="border-top-color:var(--lab-amber);">
                  <div class="rule-title">Exit Rule</div>
                  <div class="small-muted">{manifest["exit_rule"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            f"""
            <div class="callout danger-callout" style="border-left-color:var(--lab-rose);background:var(--lab-rose-soft);">
              <strong>Known failure mode:</strong> {manifest["known_failure_mode"]}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Required data**")
        st.write(", ".join(manifest["required_data"]))
        st.markdown("**What the chart must show**")
        st.write(manifest["chart_requirement"])
        with st.expander("Open raw manifest JSON"):
            st.json(manifest)

    data_scope_preview = build_workbench_data_scope_preview(manifest)
    strategy_narrative = build_workbench_strategy_narrative(manifest, data_scope_preview)
    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">02 / Readable contract</div>
          <div class="workbench-section-title">Understand the rule before seeing numbers.</div>
          <div class="workbench-section-copy">
            The lab should first say what the strategy buys, how it exits, what data is real, and what can block it.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    n1, n2, n3 = st.columns([1.25, 1, 1])
    with n1:
        st.markdown(
            f"""
            <div class="rule-card" style="border-top-color:var(--lab-blue);">
              <div class="rule-title">What it buys</div>
              <div class="strategy-copy">{strategy_narrative["plain_english_rule"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with n2:
        st.markdown(
            f"""
            <div class="rule-card" style="border-top-color:var(--lab-amber);">
              <div class="rule-title">How it exits</div>
              <div class="strategy-copy">{strategy_narrative["exit_plain_english"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with n3:
        coverage = strategy_narrative["data_coverage"]
        st.markdown(
            f"""
            <div class="rule-card" style="border-top-color:var(--lab-plum);">
              <div class="rule-title">Data actually available</div>
              <div class="metric-value" style="font-size:26px;">{coverage["local_price_symbols"]} / {coverage["configured_symbols"]}</div>
              <div class="small-muted">{coverage["local_rows"]} local OHLCV rows routed into this dry-run.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div class="callout" style="border-color:#ffd1df;border-left-color:var(--lab-rose);background:var(--lab-rose-soft);color:#831843;">
          <strong>First blocker:</strong> {strategy_narrative["failure_plain_english"]}
        </div>
        """,
        unsafe_allow_html=True,
    )
    guardrail_cols = st.columns(4)
    for index, guardrail in enumerate(strategy_narrative["guardrails"]):
        with guardrail_cols[index % 4]:
            st.markdown(
                f"""
                <div class="mini-tile" style="border-top:4px solid var(--lab-mint);">
                  <div class="semantic-badge badge-evidence">Guardrail</div>
                  <div class="small-muted">{guardrail}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("**Composable rule flow**")
    st.caption("This is the strategy as blocks, not as JSON: universe, signal, filter, entry, risk, exit, gates.")
    rule_flow = build_workbench_rule_flow(manifest)
    flow_cols = st.columns(len(rule_flow))
    color_cycle = ["var(--lab-blue)", "var(--lab-mint)", "var(--lab-amber)", "var(--lab-plum)", "var(--lab-rose)", "var(--lab-amber)", "var(--lab-mint)"]
    for index, block in enumerate(rule_flow):
        with flow_cols[index]:
            st.markdown(
                f"""
                <div class="mini-tile" style="border-top:4px solid {color_cycle[index % len(color_cycle)]};min-height:138px;">
                  <div class="eyebrow">{index + 1:02d}</div>
                  <div class="rule-title">{block["block"]}</div>
                  <div class="small-muted">{block["description"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">03 / Visual explanation</div>
          <div class="workbench-section-title">Show where the rule acts.</div>
          <div class="workbench-section-copy">
            This preview is not a performance claim. It is a visual contract: entry, exit, and the first gate must be explainable on a chart.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(strategy_candlestick_chart(build_workbench_chart_story(manifest)), width="stretch")

    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">04 / Governance path</div>
          <div class="workbench-section-title">The lab keeps the brakes visible.</div>
          <div class="workbench-section-copy">
            Every strategy has to pass through a pre-run gate, data contract, dry-run, cost realism, robustness, and final decision.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(flow_chart(build_workbench_flow_nodes(manifest)), width="stretch")

    validation_rows = validate_workbench_manifest(manifest)
    gate_valid = workbench_gate_is_valid(validation_rows)
    gate = build_workbench_pre_run_gate(manifest, validation_rows)
    manifest_signature = workbench_manifest_signature(manifest)
    if st.session_state.get("workbench_active_signature") != manifest_signature:
        st.session_state["workbench_active_signature"] = manifest_signature
        st.session_state["workbench_backtest_preview"] = None
        st.session_state["workbench_artifact_bundle"] = None

    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">05 / Validation</div>
          <div class="workbench-section-title">Before the button, the gate.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    validation_cols = st.columns(3)
    for index, row in enumerate(validation_rows.to_dict("records")):
        css = {
            "PASS": "validation-pass",
            "WARN": "validation-warn",
            "BLOCK": "validation-block",
        }.get(str(row["status"]), "validation-warn")
        with validation_cols[index % 3]:
            st.markdown(
                f"""
                <div class="rule-card {css}">
                  <div class="rule-title">{row["status"]}: {row["check"]}</div>
                  <div class="small-muted">{row["detail"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-kicker" style="margin-top:22px;">Pre-run gate draft</div>', unsafe_allow_html=True)
    gate_cols = st.columns(3)
    gate_items = [
        ("Data required", ", ".join(manifest["required_data"])),
        ("First blocker", manifest["first_gate"]),
        ("Gate status", "VALID for local dry-run" if gate_valid else "BLOCKED until validation is fixed."),
    ]
    for column, (title, body) in zip(gate_cols, gate_items):
        with column:
            st.markdown(
                f"""
                <div class="rule-card">
                  <div class="rule-title">{title}</div>
                  <div class="small-muted">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with st.expander("Open structured pre-run gate draft"):
        st.json(gate)

    st.markdown('<div class="section-kicker" style="margin-top:22px;">Data scope preview</div>', unsafe_allow_html=True)
    scope_cols = st.columns(3)
    with scope_cols[0]:
        metric_card("Data scope", data_scope_preview["data_scope"], "Universe routing before the dry-run")
    with scope_cols[1]:
        metric_card("Local prices", data_scope_preview["local_price_symbols"], ", ".join(data_scope_preview["selected_symbols"]) or "No symbols routed")
    with scope_cols[2]:
        metric_card("Configured tickers", data_scope_preview["configured_symbols"], data_scope_preview["scope_explanation"])
    st.caption(
        "Configured tickers are the research catalog. Local prices are the subset already present in archived files; missing symbols are never invented by the workbench."
    )

    readiness = build_workbench_backtest_readiness(manifest, validation_rows, st.session_state.get("workbench_backtest_preview"))
    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">05B / Backtest readiness</div>
          <div class="workbench-section-title">What remains before this can become a real governed backtest?</div>
          <div class="workbench-section-copy">
            The Workbench can explain and dry-run. A real backtest still needs a committed gate, approved data, and a separate runner.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    ready_cols = st.columns(3)
    for index, stage in enumerate(readiness["stages"]):
        color = {
            "PASS": "var(--lab-mint)",
            "WARN": "var(--lab-amber)",
            "WAIT": "var(--lab-blue)",
            "BLOCK": "var(--lab-rose)",
            "LOCKED": "var(--lab-plum)",
        }.get(str(stage["status"]), "var(--lab-line)")
        with ready_cols[index % 3]:
            st.markdown(
                f"""
                <div class="rule-card" style="border-top-color:{color};">
                  <div class="eyebrow">{stage["status"]}</div>
                  <div class="rule-title">{stage["stage"]}</div>
                  <div class="small-muted">{stage["meaning"]}</div>
                  <div class="strategy-copy" style="margin-top:8px;"><strong>Next:</strong> {stage["next_step"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.info(f"Readiness: {readiness['overall_status']} · Next action: {readiness['next_user_action']}")

    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">06 / Controlled local dry-run</div>
          <div class="workbench-section-title">Run locally, explain first, audit later.</div>
          <div class="workbench-section-copy">
            The button uses archived local data only. It does not query providers, trade, or promote anything.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    run_clicked = st.button("Run controlled local dry-run", type="primary", disabled=not gate_valid, width="stretch")
    if run_clicked:
        preview_result = build_controlled_backtest_preview(manifest, validation_rows)
        st.session_state["workbench_backtest_preview"] = preview_result
        st.session_state["workbench_artifact_bundle"] = persist_workbench_run_bundle(manifest, validation_rows, preview_result)
    if not gate_valid:
        st.warning("Backtest disabled: fix the BLOCK rows in the validation panel first.")
    preview = st.session_state.get("workbench_backtest_preview")
    if preview and preview.get("manifest_signature") != manifest_signature:
        preview = None
        st.session_state["workbench_backtest_preview"] = None
        st.session_state["workbench_artifact_bundle"] = None
    if not preview and gate_valid:
        st.info("Dry-run pending for this manifest. If you changed template, cost, universe, name, or provider permission, the old report is intentionally cleared.")
    if preview:
        if preview["status"] == "BLOCKED":
            st.error(preview["reason"])
        else:
            st.markdown(
                f"""
                <div class="dryrun-report">
                  <div class="eyebrow">Dry-run report</div>
                  <div class="dryrun-title">{preview["strategy_name"]}</div>
                  <div class="dryrun-meta">
                    <strong>Template:</strong> {preview["template"]} &nbsp;|&nbsp;
                    <strong>Universe:</strong> {preview["universe"]} &nbsp;|&nbsp;
                    <strong>Mode:</strong> {preview["analysis_mode"]} &nbsp;|&nbsp;
                    <strong>Signature:</strong> <code>{preview["manifest_signature"]}</code>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                metric_card("Dry-run status", preview["status"], preview["decision"])
            with p2:
                metric_card("Local trades", preview["simulated_trades"], "Archived prices only")
            with p3:
                metric_card("Avg net", preview["net_edge_proxy"], "After declared cost")
            with p4:
                metric_card("Verdict", preview["automatic_verdict"]["decision"], "Promotion locked false")
            result_summary = build_workbench_result_summary(preview)
            st.markdown(
                f"""
                <div class="workbench-card" style="border-top:4px solid var(--lab-mint);">
                  <div class="eyebrow">Plain-language result</div>
                  <div class="strategy-title" style="font-size:26px;">{result_summary["headline"]}</div>
                  <div class="strategy-copy">{result_summary["plain_result"]}</div>
                  <div class="strategy-copy"><strong>Primary blocker:</strong> {result_summary["primary_blocker"]}</div>
                  <div class="strategy-copy"><strong>Next best action:</strong> {result_summary["next_best_action"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            visual_diagnostics = preview.get("visual_diagnostics") or build_workbench_visual_diagnostics(preview)
            explainer = visual_diagnostics.get("result_explainer", {})
            st.markdown(
                f"""
                <div class="callout">
                  <strong>{explainer.get("headline", preview["decision"])}</strong><br/>
                  {explainer.get("explanation", preview.get("why", ""))}
                </div>
                """,
                unsafe_allow_html=True,
            )
            viz_left, viz_right = st.columns([1, 1])
            distribution_rows = pd.DataFrame(visual_diagnostics.get("trade_distribution", []))
            top_winner_rows = pd.DataFrame(visual_diagnostics.get("top_winners", []))
            with viz_left:
                st.markdown("**Trade distribution**")
                st.caption(
                    "Read this as strategy health: too many bars left of 0% means the rule usually loses; bars to the far right show rare jackpot behavior."
                )
                if not distribution_rows.empty:
                    distribution_rows = distribution_rows.copy()
                    distribution_rows["zone"] = distribution_rows["bucket"].map(
                        {
                            "<= -20%": "large loss",
                            "-20% to -10%": "loss",
                            "-10% to 0%": "small loss",
                            "0% to 10%": "small win",
                            "10% to 25%": "win",
                            "> 25%": "large win",
                        }
                    )
                    fig = px.bar(
                        distribution_rows,
                        x="bucket",
                        y="trade_count",
                        color="zone",
                        color_discrete_map={
                            "large loss": "#b42318",
                            "loss": "#d12f5f",
                            "small loss": "#d97706",
                            "small win": "#60a5fa",
                            "win": "#1f5eff",
                            "large win": "#0f9f75",
                        },
                    )
                    fig.update_layout(
                        height=310,
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#171717", family="Instrument Sans"),
                        xaxis_title="Net return bucket",
                        yaxis_title="Trades",
                        margin=dict(l=10, r=10, t=28, b=10),
                    )
                    fig.update_xaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                    fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No distribution available for this dry-run.")
            with viz_right:
                st.markdown("**Top winner contribution**")
                st.caption(
                    "Read this as fragility: if one symbol dominates positive return, the result may be a single lucky outlier rather than a repeatable rule."
                )
                if not top_winner_rows.empty:
                    fig = px.bar(
                        top_winner_rows.head(8),
                        x="symbol",
                        y="share_of_positive_net",
                        color="net_return",
                        color_continuous_scale=["#d97706", "#0f9f75"],
                        hover_data=["entry_date", "exit_date", "net_return"],
                    )
                    fig.update_layout(
                        height=310,
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#171717", family="Instrument Sans"),
                        xaxis_title="Symbol",
                        yaxis_title="Share of positive net",
                        margin=dict(l=10, r=10, t=28, b=10),
                    )
                    fig.update_coloraxes(colorbar_tickfont=dict(color="#171717"), colorbar_title_font=dict(color="#171717"))
                    fig.update_xaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                    fig.update_yaxes(tickfont=dict(color="#171717"), title_font=dict(color="#171717"), gridcolor="#e7e2d8")
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No winners available for this dry-run.")
            if preview.get("analysis_mode") == "Investment":
                diagnostics = preview.get("portfolio_diagnostics", {})
                st.markdown("**Investment / Convex Basket Diagnostics**")
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    metric_card("Total net", diagnostics.get("total_net_return", 0), "Whole basket after costs")
                with d2:
                    metric_card("Max drawdown", diagnostics.get("max_drawdown", 0), "Additive local equity drawdown")
                with d3:
                    metric_card("Top decile share", diagnostics.get("top_decile_contribution") or "n/a", "Jackpot concentration")
                with d4:
                    metric_card("Payoff ratio", diagnostics.get("payoff_ratio") or "n/a", "Avg winner / avg loser")
                st.info(
                    "Investment mode does not automatically kill a convex strategy because win rate or median trade is weak. "
                    "It asks whether the whole basket survives costs, drawdown, and outlier concentration. PDUFA/Form4/13D remain proxy simulations until real PIT event data is attached."
                )
            if preview.get("bias_warnings"):
                st.markdown("**Bias warnings**")
                for warning in preview["bias_warnings"]:
                    st.warning(f"{warning['warning_id']} ({warning['severity']}): {warning['message']}")
            st.markdown("**Annotated example trade**")
            st.caption("One generated dry-run trade, marked on the local chart. This shows what the rule actually did, not what it claims in prose.")
            annotation_story = build_workbench_trade_annotation_story(manifest, preview)
            if annotation_story.get("available"):
                st.plotly_chart(strategy_candlestick_chart(annotation_story), width="stretch")
                st.write(annotation_story.get("explanation", ""))
            else:
                st.info(annotation_story.get("reason", "No annotated trade is available for this dry-run."))
            st.markdown("**Metric dictionary**")
            st.caption("This translates the numbers into plain language so the report is not just a wall of decimals.")
            st.dataframe(pd.DataFrame(build_workbench_metric_glossary(preview)), width="stretch", hide_index=True)
            detail_cols = st.columns([1, 1])
            with detail_cols[0]:
                st.markdown("**Why this outcome**")
                st.write(preview["why"])
                st.markdown("**Assumptions frozen in this dry-run**")
                assumptions_html = "".join(f"<li>{item}</li>" for item in preview["assumptions"])
                st.markdown(f'<ul class="dryrun-list">{assumptions_html}</ul>', unsafe_allow_html=True)
                st.markdown("**Risk notes**")
                risk_html = "".join(f"<li>{item}</li>" for item in preview["risk_notes"])
                st.markdown(f'<ul class="dryrun-list">{risk_html}</ul>', unsafe_allow_html=True)
            with detail_cols[1]:
                st.markdown("**Cost and validation breakdown**")
                st.json(
                    {
                        "validation_summary": preview["validation_summary"],
                        "cost_breakdown": preview["cost_breakdown"],
                        "local_data_summary": preview.get("local_data_summary", {}),
                    }
                )
                st.markdown("**Next actions**")
                actions_html = "".join(f"<li>{item}</li>" for item in preview["next_actions"])
                st.markdown(f'<ul class="dryrun-list">{actions_html}</ul>', unsafe_allow_html=True)
            trade_rows = pd.DataFrame(preview.get("trade_rows", []))
            equity_curve = pd.DataFrame(preview.get("equity_curve", []))
            if not equity_curve.empty:
                st.markdown("**Local equity and drawdown curve**")
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=equity_curve["step"],
                        y=equity_curve["cumulative_net_return"],
                        mode="lines",
                        name="Cumulative net",
                        line=dict(color="#2563eb", width=3),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=equity_curve["step"],
                        y=equity_curve["cumulative_gross_return"],
                        mode="lines",
                        name="Cumulative gross",
                        line=dict(color="#94a3b8", width=2, dash="dot"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=equity_curve["step"],
                        y=equity_curve["drawdown"],
                        mode="lines",
                        name="Drawdown",
                        fill="tozeroy",
                        line=dict(color="#ef4444", width=2),
                    )
                )
                fig.update_layout(
                    height=320,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Trade exit order",
                    yaxis_title="Additive return",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=34, b=10),
                )
                st.plotly_chart(fig, width="stretch")
            with st.expander("Open audit tables, Markdown report, and export blueprint"):
                st.markdown("**Dry-run audit rows**")
                st.dataframe(pd.DataFrame(display_safe_records(preview["dry_run_rows"])), width="stretch", hide_index=True)
                st.markdown("**Robustness gates**")
                robustness_rows = []
                for gate_name, gate_payload in preview.get("robustness_panel", {}).items():
                    robustness_rows.append(
                        {
                            "gate": gate_name,
                            "status": gate_payload.get("status"),
                            "value": gate_payload.get("value"),
                            "detail": gate_payload.get("detail"),
                        }
                    )
                st.dataframe(pd.DataFrame(display_safe_records(robustness_rows)), width="stretch", hide_index=True)
                if not trade_rows.empty:
                    st.markdown("**Generated local trade list**")
                    st.dataframe(trade_rows, width="stretch", hide_index=True)
                st.markdown("**Markdown dry-run report**")
                st.code(preview.get("markdown_report", ""), language="markdown")
                st.markdown("**Exportable strategy blueprint**")
                st.json(build_workbench_strategy_blueprint(manifest, preview))
            st.markdown("**Governed strategy package**")
            st.caption("This prepares the files a real runner would need later. It does not execute a real backtest.")
            package_cols = st.columns([1, 1])
            with package_cols[0]:
                if st.button("Generate governed strategy package", type="secondary", width="stretch"):
                    st.session_state["workbench_strategy_package"] = persist_workbench_strategy_package(manifest, validation_rows, preview)
            with package_cols[1]:
                st.caption("Files: manifest, pre-run gate, data contract, command spec, risk policy, README, dry-run report.")
            package_preview = build_workbench_strategy_package(manifest, validation_rows, preview)
            with st.expander("Preview generated package contents"):
                st.json({filename: ("markdown/text" if filename.endswith(".md") else payload) for filename, payload in package_preview.items()})
            artifact_bundle = st.session_state.get("workbench_artifact_bundle")
            if artifact_bundle:
                st.markdown("**Persisted artifacts**")
                st.json(artifact_bundle)
            strategy_package = st.session_state.get("workbench_strategy_package")
            if strategy_package:
                st.markdown("**Persisted strategy package**")
                st.json(strategy_package)

    saved_cards = load_workbench_strategy_cards(limit=6)
    if saved_cards:
        st.markdown(
            """
            <div class="workbench-section">
              <div class="section-kicker">07 / Saved strategy cards</div>
              <div class="workbench-section-title">Every dry-run becomes an auditable card.</div>
              <div class="workbench-section-copy">
                These are saved workbench artifacts, not promoted strategies. They let you compare ideas without losing the gate trail.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_cols = st.columns(3)
        for index, card in enumerate(saved_cards):
            with card_cols[index % 3]:
                net_pct = float(card["net_return_sum"]) * 100
                st.markdown(
                    f"""
                    <div class="rule-card" style="border-top-color:var(--lab-plum);">
                      <div class="eyebrow">{card["template"]} / {card["analysis_mode"]}</div>
                      <div class="rule-title">{card["strategy_name"]}</div>
                      <div class="strategy-copy"><strong>Decision:</strong> {card["decision"]}</div>
                      <div class="strategy-copy"><strong>Trades:</strong> {card["simulated_trades"]}</div>
                      <div class="strategy-copy"><strong>Net sum:</strong> {net_pct:.2f}%</div>
                      <div class="small-muted">{card["artifact_dir"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        comparison = build_workbench_comparison_table(saved_cards)
        st.markdown("**Saved run comparison**")
        st.caption("Sorted by net return, but still diagnostic only: every row remains promotion-locked.")
        st.dataframe(comparison, width="stretch", hide_index=True)

    saved_packages = load_workbench_strategy_packages(limit=8)
    st.markdown(
        """
        <div class="workbench-section">
          <div class="section-kicker">08 / Package Inspector</div>
          <div class="workbench-section-title">Inspect saved governed packages before any runner exists.</div>
          <div class="workbench-section-copy">
            A package can be ready for runner build while still forbidding execution, paper trading, live trading, and promotion.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not saved_packages:
        st.info("No governed strategy packages saved yet. Run a dry-run, then press Generate governed strategy package.")
    else:
        package_table = pd.DataFrame(saved_packages)
        st.dataframe(package_table[["strategy_name", "template", "analysis_mode", "status", "execution_allowed", "promotion_allowed"]], width="stretch", hide_index=True)
        labels = [f"{row['strategy_name']} · {row['manifest_signature']}" for row in saved_packages]
        selected_label = st.selectbox("Inspect package", labels)
        selected_package = saved_packages[labels.index(selected_label)]
        inspection = inspect_workbench_strategy_package(Path(selected_package["package_dir"]))
        i1, i2, i3 = st.columns(3)
        with i1:
            metric_card("Package status", inspection["status"], "Runner readiness, not execution permission")
        with i2:
            metric_card("Execution", inspection["command_spec"].get("execution_allowed", False), "Must remain false here")
        with i3:
            metric_card("Promotion", inspection["risk_policy"].get("promotion_allowed", False), "Must remain false here")
        st.markdown("**Readiness checks**")
        st.dataframe(pd.DataFrame(inspection["readiness_rows"]), width="stretch", hide_index=True)
        st.markdown("**Diagnostic runner**")
        runner_cols = st.columns([1, 1, 1])
        with runner_cols[0]:
            metric_card("Runner output", "available" if inspection["runner_available"] else "not run", inspection["runner_output_dir"])
        with runner_cols[1]:
            if st.button("Run diagnostic package runner", type="secondary", width="stretch"):
                st.session_state["workbench_last_runner_paths"] = run_package_diagnostic(Path(selected_package["package_dir"]))
                inspection = inspect_workbench_strategy_package(Path(selected_package["package_dir"]))
        with runner_cols[2]:
            st.caption("Local diagnostic only: no provider query, no paper/live, no promotion.")
        if inspection["runner_available"]:
            r1, r2, r3 = st.columns(3)
            with r1:
                metric_card("Final decision", inspection["runner_decision"].get("decision", "UNKNOWN"), "Runner artifact")
            with r2:
                metric_card("Trades", inspection["runner_decision"].get("simulated_trades", 0), "Local diagnostic run")
            with r3:
                metric_card("Net sum", inspection["runner_decision"].get("net_return_sum", "n/a"), "After declared costs")
        runner_paths = st.session_state.get("workbench_last_runner_paths")
        if runner_paths:
            st.markdown("**Last runner artifact paths**")
            st.json(runner_paths)
        package_tabs = st.tabs(["README", "Manifest", "Data Contract", "Command Spec", "Risk Policy", "Dry-Run Report", "Runner Artifacts"])
        with package_tabs[0]:
            st.markdown(inspection["readme"])
        with package_tabs[1]:
            st.json(inspection["manifest"])
        with package_tabs[2]:
            st.json(inspection["data_contract"])
        with package_tabs[3]:
            st.json(inspection["command_spec"])
        with package_tabs[4]:
            st.json(inspection["risk_policy"])
        with package_tabs[5]:
            st.code(inspection["dry_run_report"], language="markdown")
        with package_tabs[6]:
            if inspection["runner_available"]:
                st.json(
                    {
                        "final_decision": inspection["runner_decision"],
                        "summary": inspection["runner_summary"],
                        "runner_audit": inspection["runner_audit"],
                    }
                )
            else:
                st.info("No diagnostic runner artifact yet.")
        st.info("This adapter is the first real end-to-end diagnostic runner, but it still cannot paper trade, live trade, query providers, or promote.")

    st.subheader("What The Builder Will Enforce")
    checks = [
        ("Pre-run gate first", "No backtest and no provider query before the manifest is frozen."),
        ("Data contract", "The UI must declare whether the strategy needs PIT, RTH, delisted, or intraday data."),
        ("Cost realism", "The selected cost model is part of the hypothesis, not an after-the-fact adjustment."),
        ("No silent promotion", "The workbench can generate candidates, but promotion stays false until gates pass."),
    ]
    st.markdown('<div class="capability-grid">', unsafe_allow_html=True)
    for title, body in checks:
        st.markdown(
            f"""
            <div class="capability">
              <div class="strategy-family">Workbench guardrail</div>
              <div style="font-family:Exo,system-ui,sans-serif;font-weight:800;margin:8px 0;">{title}</div>
              <div class="small-muted">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Open full template library"):
        template_rows = []
        for template_name, template_data in WORKBENCH_TEMPLATES.items():
            template_rows.append(
                {
                    "template": template_name,
                    "signal": template_data["signal"],
                    "first_gate": template_data["default_gate"],
                    "known_failure_mode": template_data["failure_mode"],
                }
            )
        st.dataframe(pd.DataFrame(template_rows), width="stretch", hide_index=True)


def render_portfolio_lab(payload: dict[str, object]) -> None:
    st.markdown(
        """
        <div class="portfolio-hero">
          <div>
            <div class="lab-kicker">WORKBENCH-PORTFOLIO-001</div>
            <h1>Stop hunting one perfect setup.</h1>
            <p>
              Portfolio Lab composes saved Workbench dry-runs and asks whether imperfect strategy components
              become more robust together after costs, correlation, drawdown, and best-component removal.
            </p>
          </div>
          <div class="portfolio-hero-note">
            <strong>Research console, not a launchpad.</strong>
            <span>Diagnostic only: no provider query, no market-data download, no paper trading, no live trading, and no promotion.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page_guide(
        "How to use Portfolio Lab",
        "This page has two jobs: inspect a basket you select manually, and run a bounded factory search over locally testable strategy components. It is still a diagnostic console, not a trading system.",
        [
            ("Setup", "Choose whether generated components enter the catalog and whether the regime router filters them.", "data"),
            ("Verdict", "Read the current basket summary: components, net, drawdown, and blockers.", "warn"),
            ("Dynamic path", "Compare static allocation with regime-switching allocation through time.", "good"),
            ("Next gate", "Only after preregistration can the lab create a dry-run, frozen recipe, or data contract.", "block"),
        ],
    )
    with st.expander("1. Setup catalog and market regime", expanded=True):
        factory_cols = st.columns([1, 1, 2])
        with factory_cols[0]:
            include_factory_generated = st.checkbox("Include generated catalog", value=True)
        with factory_cols[1]:
            factory_variant_limit = st.slider("Generated variants", 24, 240, 48, 24)
        with factory_cols[2]:
            section_note("Generated catalog means strategies produced from frozen templates and currently available local/proxy data. No provider query, no promotion.")
        run_full_catalog = st.checkbox("Run governed search on full loaded catalog", value=include_factory_generated)
    strategy_router = payload.get("strategy_regime_router", {})
    current_regime = payload.get("current_market_regime", {})
    router_matrix = strategy_router.get("matrix", pd.DataFrame()) if isinstance(strategy_router, dict) else pd.DataFrame()
    available_regimes = (
        sorted(str(item) for item in router_matrix["regime_label"].dropna().unique())
        if isinstance(router_matrix, pd.DataFrame) and not router_matrix.empty and "regime_label" in router_matrix.columns
        else []
    )
    detected_regime = str(current_regime.get("regime_label", "RANGE_NORMAL")) if isinstance(current_regime, dict) else "RANGE_NORMAL"
    default_regime = detected_regime if detected_regime in available_regimes else ("RANGE_NORMAL" if "RANGE_NORMAL" in available_regimes else (available_regimes[0] if available_regimes else "RANGE_NORMAL"))
    router_cols = st.columns([1, 1, 2])
    with router_cols[0]:
        use_regime_router = st.checkbox("Use regime router", value=True)
    with router_cols[1]:
        active_regime = st.selectbox(
            "Active market regime",
            available_regimes or ["RANGE_NORMAL"],
            index=((available_regimes or ["RANGE_NORMAL"]).index(default_regime)),
            disabled=not use_regime_router,
        )
    with router_cols[2]:
        section_note("Regime-aware mode defaults to the latest local regime-map majority vote, then lets you override it manually.")
    if isinstance(current_regime, dict):
        st.markdown("**Detected market regime**")
        detected_cols = st.columns(3)
        with detected_cols[0]:
            metric_card("Detected", current_regime.get("regime_label", "UNKNOWN"), "Latest local majority vote")
        with detected_cols[1]:
            metric_card("Confidence", f"{float(current_regime.get('confidence', 0.0)):.0%}", f"{current_regime.get('symbol_count', 0)} symbols")
        with detected_cols[2]:
            metric_card("As of", current_regime.get("as_of_date", "n/a"), "Local regime map date")
        st.caption(str(current_regime.get("interpretation", "")))
    eligibility = cached_factory_data_eligibility_report()
    excluded_templates = eligibility.get("excluded_templates", [])
    st.markdown(
        f"""
        <div class="portfolio-proof-grid">
          <div class="portfolio-proof-card good">
            <div class="eyebrow">Factory eligibility</div>
            <div class="portfolio-proof-title">{eligibility.get("eligible_count", 0)} template(s) allowed</div>
            <div class="portfolio-proof-copy">Only strategies with a locally testable data contract enter the combinatorial search.</div>
          </div>
          <div class="portfolio-proof-card block">
            <div class="eyebrow">Data blockers</div>
            <div class="portfolio-proof-title">{eligibility.get("excluded_count", 0)} template(s) excluded</div>
            <div class="portfolio-proof-copy">Blocked templates remain visible, but they cannot pollute the best-basket search with untestable proxy returns.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if excluded_templates:
        with st.expander("Show templates excluded from Factory search"):
            st.dataframe(pd.DataFrame(excluded_templates), width="stretch", hide_index=True)

    components = load_portfolio_lab_components(limit=60)
    if include_factory_generated:
        components = [*components, *cached_strategy_factory_components(factory_variant_limit)]
    if not components:
        st.warning("No saved Workbench components found yet. Create and dry-run strategies first.")
        return

    labels = {
        component["component_id"]: f"{component['strategy_name']} · {component['template']} · {component['component_id']}"
        for component in components
    }
    default_ids = [component["component_id"] for component in components[: min(6, len(components))]]
    if "portfolio_lab_selected_ids" not in st.session_state:
        st.session_state["portfolio_lab_selected_ids"] = default_ids
    if "portfolio_lab_pending_selected_ids" in st.session_state:
        st.session_state["portfolio_lab_selected_ids"] = list(st.session_state.pop("portfolio_lab_pending_selected_ids"))
    st.session_state["portfolio_lab_selected_ids"] = [
        component_id for component_id in st.session_state["portfolio_lab_selected_ids"] if component_id in labels
    ] or default_ids
    st.markdown(
        """
        <div class="workbench-section">
          <div class="lab-kicker">01 / Component Basket</div>
          <div class="workbench-section-title">Choose the saved strategy components.</div>
          <div class="workbench-section-copy">
            This selector is the current basket you are inspecting. When generated catalog is enabled,
            the list includes strategies you never manually created, produced from frozen templates and guarded local dry-runs.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_ids = st.multiselect(
        "Current selected basket",
        options=list(labels),
        default=st.session_state["portfolio_lab_selected_ids"],
        format_func=lambda component_id: labels.get(component_id, component_id),
        key="portfolio_lab_selected_ids",
    )
    st.caption("Current basket only. Use the governed-search button below to load the suggested best basket into this selector.")
    selected_components = [component for component in components if component["component_id"] in selected_ids]
    component_table = portfolio_lab_component_table(selected_components)
    if not component_table.empty:
        st.dataframe(component_table, width="stretch", hide_index=True)
    if run_full_catalog:
        st.info(f"Full-catalog mode is active: the diagnostic below ignores the selector and evaluates all {len(components)} loaded components after dedupe. The selector is only for inspection.")

    st.markdown(
        """
        <div class="workbench-section">
          <div class="lab-kicker">02 / Allocation Contract</div>
          <div class="workbench-section-title">Set weights before seeing the verdict.</div>
          <div class="workbench-section-copy">
            Avoid historical Sharpe optimization. The first portfolio diagnostic should use simple,
            explainable weights that cannot torture the past into a pretty curve.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    with cols[0]:
        policy = st.selectbox("Allocation policy", ["sleeve_allocation", "equal_weight", "inverse_volatility"], index=0)
    with cols[1]:
        max_component_weight = st.slider("Max component weight", 0.10, 0.80, 0.60, 0.05)
    with cols[2]:
        max_rejected_weight = st.slider("Max rejected weight", 0.00, 0.40, 0.20, 0.05)
    with cols[3]:
        max_convex_weight = st.slider("Max convex sleeve", 0.00, 0.50, 0.20, 0.05)

    if not selected_ids and not run_full_catalog:
        st.info("Select at least three components to run a toy portfolio diagnostic.")
        return

    diagnostic_base_components = components if run_full_catalog else selected_components
    regime_filter = None
    if use_regime_router:
        regime_filter = build_regime_aware_portfolio_component_set(diagnostic_base_components, strategy_router, active_regime)
        diagnostic_components = list(regime_filter.get("allowed_components", []))
        blocked_count = len(regime_filter.get("blocked_components", []))
        st.markdown("**Regime-aware component contract**")
        c_allowed, c_blocked, c_regime = st.columns(3)
        with c_allowed:
            metric_card("Allowed", len(diagnostic_components), "Components entering diagnostic")
        with c_blocked:
            metric_card("Blocked", blocked_count, "Blocked or observe-only sleeves")
        with c_regime:
            metric_card("Active regime", active_regime, "Router state")
        if blocked_count:
            st.caption("The blocked components stay visible in the selector, but they are excluded from the diagnostic basket for this regime.")
            with st.expander("Show regime filter contract"):
                st.dataframe(pd.DataFrame(regime_filter.get("contract_rows", [])), width="stretch", hide_index=True)
        if not diagnostic_components:
            st.warning("The regime router blocked every selected component. Choose another regime, expand the catalog, or add a Regime Filter component.")
            return
    else:
        diagnostic_components = components
    diagnostic_selected_ids = None if (run_full_catalog or use_regime_router) else selected_ids
    preview = build_portfolio_lab_preview_from_components(
        diagnostic_components,
        diagnostic_selected_ids,
        policy=policy,
        max_component_weight=max_component_weight,
        max_rejected_weight=max_rejected_weight,
        max_convex_weight=max_convex_weight,
    )
    if regime_filter:
        preview["regime_router_contract"] = {
            "status": regime_filter.get("status"),
            "active_regime": regime_filter.get("active_regime"),
            "allowed_component_count": len(regime_filter.get("allowed_components", [])),
            "blocked_component_count": len(regime_filter.get("blocked_components", [])),
            "contract_rows": regime_filter.get("contract_rows", []),
            "promotion_allowed": False,
            "provider_query_performed": False,
            "backtest_performed": False,
        }
    summary = preview["summary"]
    decision = preview["final_decision"]
    st.markdown(
        """
        <div class="workbench-section">
          <div class="lab-kicker">03 / Portfolio Verdict</div>
          <div class="workbench-section-title">Diversification is tested, not assumed.</div>
          <div class="workbench-section-copy">
            The gates ask whether the basket survives concentration, costs, drawdown,
            common-factor correlation, and removal of the best component.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    result_cols = st.columns(4)
    with result_cols[0]:
        metric_card("Components", summary["component_count"], "Allocated components in diagnostic")
    with result_cols[1]:
        metric_card("Net sum", f"{summary['total_net_return']:.2f}", "Weighted diagnostic return")
    with result_cols[2]:
        metric_card("Max drawdown", f"{summary['max_drawdown']:.2f}", "Worst local decline")
    with result_cols[3]:
        metric_card("Decision", decision["decision"], "Promotion locked false")

    if decision["blockers"]:
        st.error("Portfolio blockers: " + ", ".join(decision["blockers"]))
    else:
        st.success("No hard portfolio blocker fired, but the diagnostic remains non-promotable.")
    source_summary = preview.get("component_source_summary", {})
    factory_lineage_count = source_summary.get("factory_generated", 0) + source_summary.get("factory_materialized", 0)
    st.caption(
        f"Component sources in this diagnostic: saved workbench = {source_summary.get('saved_workbench', 0)}, "
        f"factory generated = {source_summary.get('factory_generated', 0)}, "
        f"factory materialized = {source_summary.get('factory_materialized', 0)}."
    )
    if regime_filter:
        st.caption(
            f"Regime router applied: {regime_filter.get('active_regime')} | "
            f"allowed {len(regime_filter.get('allowed_components', []))} / "
            f"blocked {len(regime_filter.get('blocked_components', []))}. "
            "This is a preprocessing guard, not optimization evidence."
        )
    switching = build_regime_switching_portfolio_diagnostic(diagnostic_base_components, payload.get("regime_map", pd.DataFrame()), strategy_router)
    preview["regime_switching_diagnostic"] = switching
    if switching.get("status") == "REGIME_SWITCHING_PORTFOLIO_DIAGNOSTIC_ONLY":
        st.markdown(
            """
            <div class="workbench-section">
              <div class="lab-kicker">04 / Dynamic Regime Switching</div>
              <div class="workbench-section-title">Now the portfolio changes through time.</div>
              <div class="workbench-section-copy">
                This diagnostic replays the local return streams and changes eligible sleeves whenever the local regime map changes.
                It compares that adaptive path with a static equal-weight basket on the same component set.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        switch_summary = switching.get("summary", {})
        switch_cols = st.columns(4)
        with switch_cols[0]:
            metric_card("Dynamic net", f"{switch_summary.get('dynamic_total_net_return', 0.0):.2f}", "Regime-switched path")
        with switch_cols[1]:
            metric_card("Static net", f"{switch_summary.get('static_total_net_return', 0.0):.2f}", "Equal basket baseline")
        with switch_cols[2]:
            metric_card("Delta", f"{switch_summary.get('dynamic_vs_static_delta', 0.0):.2f}", "Dynamic minus static")
        with switch_cols[3]:
            metric_card("Dynamic DD", f"{switch_summary.get('dynamic_max_drawdown', 0.0):.2f}", "Worst local decline")
        if float(switch_summary.get("dynamic_vs_static_delta", 0.0) or 0.0) < 0:
            st.warning(
                "The dynamic regime-switching path is weaker than the static proxy basket on this local surface. "
                "That does not invalidate the router, but it means the current regime rules are defensive diagnostics, not proven return enhancement."
            )
        else:
            st.info("The dynamic path beats the static proxy basket on this local surface, but it remains non-promotable until a true data gate exists.")
        dynamic_curve = pd.DataFrame(switching.get("dynamic_curve", []))
        static_curve = pd.DataFrame(switching.get("static_curve", []))
        if not dynamic_curve.empty and not static_curve.empty:
            dyn_plot = dynamic_curve[["period", "cumulative_net_return"]].copy()
            dyn_plot["path"] = "dynamic regime-switching"
            static_plot = static_curve[["period", "cumulative_net_return"]].copy()
            static_plot["path"] = "static equal basket"
            plot_frame = pd.concat([dyn_plot, static_plot], ignore_index=True)
            fig = px.line(
                plot_frame,
                x="period",
                y="cumulative_net_return",
                color="path",
                color_discrete_map={"dynamic regime-switching": "#0f9f75", "static equal basket": "#71717a"},
            )
            fig.update_layout(
                template="plotly_white",
                height=380,
                margin=dict(l=0, r=0, t=10, b=10),
                xaxis_title="Period",
                yaxis_title="Cumulative local net",
                paper_bgcolor="rgba(255,255,255,.72)",
                plot_bgcolor="rgba(255,255,255,.72)",
                font=dict(color="#171717", family="Instrument Sans"),
                legend_title_text="Path",
            )
            fig.update_xaxes(tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            fig.update_yaxes(tickfont=dict(color="#3f3f46"), title_font=dict(color="#71717a"), gridcolor="#e7e2d8")
            st.plotly_chart(fig, width="stretch")
        usage = pd.DataFrame(switching.get("regime_usage", []))
        if not usage.empty:
            with st.expander("Show dynamic regime usage"):
                st.dataframe(usage, width="stretch", hide_index=True)
                st.dataframe(dynamic_curve[["period", "active_regime", "portfolio_return", "cumulative_net_return", "drawdown"]], width="stretch", hide_index=True)
    if factory_lineage_count:
        st.warning(
            "Factory-generated or factory-materialized components are idea discovery only. The best basket can suggest a recipe, "
            "but it cannot be treated as a research candidate until those components are converted into "
            "a manually approved pre-registered portfolio trial."
        )

    dedupe = preview.get("strategy_deduplication", {})
    search = preview.get("portfolio_search", {})
    st.markdown("**Automatic portfolio hygiene**")
    st.markdown(
        f"""
        <div class="portfolio-proof-grid">
          <div class="portfolio-proof-card good">
            <div class="eyebrow">Duplicate control</div>
            <div class="portfolio-proof-title">{dedupe.get("removed_component_count", 0)} strategy duplicate(s) removed</div>
            <div class="portfolio-proof-copy">Same generated recipes and near-identical return paths are treated as one hidden bet before the search reads them.</div>
          </div>
          <div class="portfolio-proof-card warn">
            <div class="eyebrow">Governed search</div>
            <div class="portfolio-proof-title">{search.get("evaluated_candidate_count", 0)} bounded basket(s) evaluated</div>
            <div class="portfolio-proof-copy">The objective is fixed in code: validation-weighted return after cost stress, ex-best removal, concentration and correlation penalties.</div>
          </div>
          <div class="portfolio-proof-card block">
            <div class="eyebrow">Overfit guard</div>
            <div class="portfolio-proof-title">Promotion stays locked</div>
            <div class="portfolio-proof-copy">The best basket is a diagnostic suggestion only. It cannot become a tradable edge without a separately pre-registered backtest.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if dedupe.get("groups"):
        with st.expander("Show eliminated equivalent strategies"):
            st.dataframe(pd.DataFrame(dedupe["groups"]), width="stretch", hide_index=True)
    if search.get("search_performed"):
        best = search.get("best_summary", {})
        st.markdown("**Best governed basket found locally**")
        best_cols = st.columns(4)
        with best_cols[0]:
            metric_card("Best components", best.get("component_count", 0), "After dedupe and bounded search")
        with best_cols[1]:
            metric_card("Best net", f"{best.get('total_net_return', 0.0):.2f}", "Diagnostic weighted sum")
        with best_cols[2]:
            metric_card("Validation net", f"{best.get('validation_net_return', 0.0):.2f}", "Later half of local return path")
        with best_cols[3]:
            metric_card("Ex-best", f"{best.get('ex_best_net_return', 0.0):.2f}", "After removing strongest component")
        st.caption("Best governed basket components: " + ", ".join(search.get("best_component_labels", [])))
        best_ids = set(search.get("best_basket_component_ids", []))
        best_source_by_id = {str(component.get("component_id")): str(component.get("source", "saved_workbench")) for component in components}
        if any(best_source_by_id.get(component_id) in {"factory_generated", "factory_materialized"} for component_id in best_ids):
            st.warning(
                "This best basket contains generated or materialized factory strategies. Read it as a hypothesis recipe: "
                "promote nothing, approve the pre-registration draft, then rerun as a separate portfolio trial."
            )
        draft_type = st.radio(
            "Pre-registration type",
            ["Static Portfolio Candidate", "Dynamic Regime-Switching Candidate"],
            horizontal=True,
            help="Dynamic freezes regime-router activation rules and adds dynamic-vs-static falsification gates.",
        )
        best_actions = st.columns(3)
        with best_actions[0]:
            if st.button("Load best governed basket into selector", type="secondary", width="stretch"):
                st.session_state["portfolio_lab_pending_selected_ids"] = list(search.get("best_basket_component_ids", []))
                st.rerun()
        with best_actions[1]:
            if st.button("Materialize generated best basket", type="secondary", width="stretch"):
                result = materialize_factory_components_as_workbench_runs(
                    components,
                    list(search.get("best_basket_component_ids", [])),
                    root=REPO_ROOT,
                )
                st.session_state["portfolio_lab_materialization_result"] = result
                st.rerun()
        with best_actions[2]:
            if st.button("Create pre-registration draft", type="primary", width="stretch"):
                candidate_type = "dynamic_regime_switching" if draft_type == "Dynamic Regime-Switching Candidate" else "static_portfolio"
                draft = build_portfolio_preregistration_draft(
                    components,
                    list(search.get("best_basket_component_ids", [])),
                    source_search={
                        "selection_rule": search.get("selection_rule"),
                        "objective": search.get("objective"),
                        "evaluated_candidate_count": search.get("evaluated_candidate_count"),
                        "best_summary": search.get("best_summary", {}),
                        "best_component_labels": search.get("best_component_labels", []),
                    },
                    candidate_type=candidate_type,
                    regime_switching_diagnostic=switching if candidate_type == "dynamic_regime_switching" else None,
                )
                paths = persist_portfolio_preregistration_draft(draft, root=REPO_ROOT)
                st.session_state["portfolio_lab_preregistration_result"] = {"draft": draft, "paths": paths}
                st.rerun()
        if "portfolio_lab_materialization_result" in st.session_state:
            materialization = st.session_state["portfolio_lab_materialization_result"]
            st.success(
                f"Materialized {materialization.get('materialized_count', 0)} generated component(s) as Workbench diagnostic artifacts. "
                "Factory provenance warnings were retained."
            )
            if materialization.get("skipped_count", 0):
                st.warning(f"Skipped {materialization.get('skipped_count')} component(s): {materialization.get('skipped')}")
        if "portfolio_lab_preregistration_result" in st.session_state:
            prereg = st.session_state["portfolio_lab_preregistration_result"]
            draft = prereg.get("draft", {})
            paths = prereg.get("paths", {})
            st.success(
                f"Pre-registration draft created: {draft.get('trial_id', 'UNKNOWN')}. "
                "Manual approval is still required before any portfolio trial can count as evidence."
            )
            st.caption(f"Vault files: {paths.get('json_path', '')} and {paths.get('markdown_path', '')}")
            with st.expander("Open pre-registration draft summary"):
                st.json(
                    {
                        "status": draft.get("status"),
                        "candidate_type": draft.get("candidate_type"),
                        "regime_switching_contract": draft.get("regime_switching_contract", {}),
                        "anti_overfit_disclosures": draft.get("anti_overfit_disclosures", []),
                        "template_mix": draft.get("template_mix", []),
                        "falsification_criteria": draft.get("falsification_criteria", []),
                        "required_next_step": draft.get("required_next_step"),
                    }
                )
            if st.button("Approve draft gate for separate portfolio trial", type="secondary", width="stretch"):
                gate = build_portfolio_preregistration_approval_gate(
                    draft,
                    approved_by="local_user",
                    approval_note="Approved from Portfolio Lab UI for separate dry-run only.",
                )
                gate_paths = persist_portfolio_preregistration_approval_gate(gate, root=REPO_ROOT)
                st.session_state["portfolio_lab_preregistration_approval"] = {"gate": gate, "paths": gate_paths}
                st.rerun()
        if "portfolio_lab_preregistration_approval" in st.session_state:
            approval = st.session_state["portfolio_lab_preregistration_approval"]
            gate = approval.get("gate", {})
            paths = approval.get("paths", {})
            st.success(
                f"Approval gate written: {gate.get('status', 'UNKNOWN')}. "
                "Next allowed action is a separate portfolio trial dry-run only."
            )
            st.caption(f"Approval gate file: {paths.get('approval_gate_path', '')}")
            if st.button("Run separate portfolio trial dry-run", type="primary", width="stretch"):
                prereg = st.session_state.get("portfolio_lab_preregistration_result", {})
                draft = prereg.get("draft", {})
                trial = build_separate_portfolio_trial_dry_run(
                    draft,
                    gate,
                    components,
                    policy=policy,
                    regime_map=payload.get("regime_map", pd.DataFrame()),
                    strategy_router=strategy_router,
                )
                trial_paths = persist_separate_portfolio_trial_dry_run(trial, root=REPO_ROOT)
                st.session_state["portfolio_lab_separate_trial_result"] = {"trial": trial, "paths": trial_paths}
                st.rerun()
        if "portfolio_lab_separate_trial_result" in st.session_state:
            separate_trial = st.session_state["portfolio_lab_separate_trial_result"]
            trial = separate_trial.get("trial", {})
            paths = separate_trial.get("paths", {})
            final = trial.get("final_decision", {})
            if trial.get("status") in {"SEPARATE_PORTFOLIO_TRIAL_DRY_RUN_COMPLETE", "DYNAMIC_REGIME_SWITCHING_TRIAL_DRY_RUN_COMPLETE"}:
                st.success(
                    f"Separate portfolio trial dry-run complete: {final.get('decision', 'UNKNOWN')} "
                    f"({trial.get('candidate_type', 'static_portfolio')}). "
                    "Promotion remains locked."
                )
                if trial.get("candidate_type") == "dynamic_regime_switching":
                    switch_summary = trial.get("regime_switching_diagnostic", {}).get("summary", {})
                    st.caption(
                        f"Dynamic trial delta vs static proxy: {float(switch_summary.get('dynamic_vs_static_delta', 0.0)):.2f}; "
                        f"dynamic drawdown {float(switch_summary.get('dynamic_max_drawdown', 0.0)):.2f}."
                    )
                if trial.get("candidate_type") != "dynamic_regime_switching" and st.button("Freeze recipe and run validation split", type="secondary", width="stretch"):
                    approval = st.session_state.get("portfolio_lab_preregistration_approval", {})
                    gate = approval.get("gate", {})
                    frozen = build_portfolio_frozen_recipe_trial(trial, gate, components)
                    frozen_paths = persist_portfolio_frozen_recipe_trial(frozen, root=REPO_ROOT)
                    st.session_state["portfolio_lab_frozen_recipe_result"] = {"trial": frozen, "paths": frozen_paths}
                    st.rerun()
            else:
                st.error(f"Separate portfolio trial blocked: {trial.get('status', 'UNKNOWN')}")
            st.caption(f"Trial files: {paths.get('trial_report_path', '')} and {paths.get('final_decision_path', '')}")
        if "portfolio_lab_frozen_recipe_result" in st.session_state:
            frozen_result = st.session_state["portfolio_lab_frozen_recipe_result"]
            frozen = frozen_result.get("trial", {})
            paths = frozen_result.get("paths", {})
            split = frozen.get("validation_split", {})
            final = frozen.get("final_decision", {})
            st.info(
                f"Frozen recipe validation: {final.get('decision', 'UNKNOWN')}. "
                f"Validation net {float(split.get('validation_net_return', 0.0)):.2f}; "
                "promotion remains locked."
            )
            frozen_cols = st.columns(4)
            with frozen_cols[0]:
                metric_card("Train net", f"{float(split.get('train_net_return', 0.0)):.2f}", "First half")
            with frozen_cols[1]:
                metric_card("Validation net", f"{float(split.get('validation_net_return', 0.0)):.2f}", "Later half")
            with frozen_cols[2]:
                metric_card("Validation DD", f"{float(split.get('validation_max_drawdown', 0.0)):.2f}", "Later half pain")
            with frozen_cols[3]:
                metric_card("Max weight", f"{float(frozen.get('weight_contract', {}).get('max_component_weight', 0.0)):.0%}", "No optimization")
            st.caption(f"Frozen files: {paths.get('trial_report_path', '')} and {paths.get('final_decision_path', '')}")
            if st.button("Create true-backtest data gate", type="secondary", width="stretch"):
                data_gate = build_portfolio_external_data_backtest_gate(frozen)
                data_gate_paths = persist_portfolio_external_data_backtest_gate(data_gate, root=REPO_ROOT)
                st.session_state["portfolio_lab_external_data_gate_result"] = {"gate": data_gate, "paths": data_gate_paths}
                st.rerun()
            if st.button("Create manual composite hypothesis", type="secondary", width="stretch"):
                manual = build_portfolio_manual_composite_trial(frozen)
                manual_paths = persist_portfolio_manual_composite_trial(manual, root=REPO_ROOT)
                st.session_state["portfolio_lab_manual_composite_result"] = {"trial": manual, "paths": manual_paths}
                st.rerun()
        if "portfolio_lab_manual_composite_result" in st.session_state:
            manual_result = st.session_state["portfolio_lab_manual_composite_result"]
            manual = manual_result.get("trial", {})
            paths = manual_result.get("paths", {})
            manifest = manual.get("manual_manifest", {})
            st.success(
                f"Manual composite written: {manifest.get('strategy_name', 'Manual Composite')}. "
                "Factory-scope blocker removed, external-data gate remains."
            )
            st.caption(f"Manual files: {paths.get('manifest_path', '')} and {paths.get('final_decision_path', '')}")
            with st.expander("Open manual composite sleeves"):
                st.json(
                    {
                        "hypothesis": manifest.get("hypothesis", ""),
                        "sleeves": manifest.get("sleeves", []),
                        "falsification_criteria": manifest.get("falsification_criteria", []),
                        "final_decision": manual.get("final_decision", {}),
                    }
                )
        if "portfolio_lab_external_data_gate_result" in st.session_state:
            data_gate_result = st.session_state["portfolio_lab_external_data_gate_result"]
            data_gate = data_gate_result.get("gate", {})
            paths = data_gate_result.get("paths", {})
            st.warning(
                f"True backtest gate: {data_gate.get('status', 'UNKNOWN')}. "
                "No provider query or market-data download is allowed until an admissible PIT/delisted source is selected."
            )
            st.caption(f"Data gate files: {paths.get('gate_path', '')} and {paths.get('final_decision_path', '')}")
            with st.expander("Open required external-data contract"):
                st.json(
                    {
                        "required_before_backtest": data_gate.get("required_before_backtest", []),
                        "provider_candidates": data_gate.get("provider_candidates", []),
                        "minimum_backtest_contract": data_gate.get("minimum_backtest_contract", {}),
                    }
                )
        comparison_path = (
            REPO_ROOT
            / "experiments/provider_aware_research/execution_outputs/PORTFOLIO-CANDIDATE-COMPARISON-001/PORTFOLIO-CANDIDATE-COMPARISON-001/candidate_comparison.json"
        )
        if comparison_path.exists():
            if st.button("Select Candidate 002 for data-gate review", type="secondary", width="stretch"):
                comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
                manual = st.session_state.get("portfolio_lab_manual_composite_result", {}).get("trial")
                data_gate = st.session_state.get("portfolio_lab_external_data_gate_result", {}).get("gate")
                state = build_portfolio_candidate_primary_research_state(comparison, manual=manual, data_gate=data_gate)
                state_paths = persist_portfolio_candidate_primary_research_state(state, root=REPO_ROOT)
                st.session_state["portfolio_lab_primary_research_state"] = {"state": state, "paths": state_paths}
                st.rerun()
        primary_state = st.session_state.get("portfolio_lab_primary_research_state", {}).get("state")
        primary_paths = st.session_state.get("portfolio_lab_primary_research_state", {}).get("paths", {})
        if primary_state is None:
            primary_state = load_portfolio_candidate_primary_research_state(root=REPO_ROOT)
        if primary_state:
            selected = primary_state.get("selected_candidate", {})
            deltas = primary_state.get("comparison_deltas", {})
            st.markdown("**Primary research candidate**")
            st.info(
                f"{primary_state.get('selected_candidate_id', 'Candidate')} is selected for data-gate review only. "
                "This is not a promotion, not a backtest, and not paper/live trading permission."
            )
            candidate_cols = st.columns(4)
            with candidate_cols[0]:
                metric_card("Components", selected.get("component_count", 0), "Frozen hypothesis mix")
            with candidate_cols[1]:
                metric_card("Validation delta", f"{float(deltas.get('validation_net_return_delta', 0.0)):.2f}", "Vs Candidate 001")
            with candidate_cols[2]:
                metric_card("DD improvement", f"{float(deltas.get('max_drawdown_improvement', 0.0)):.2f}", "Less local pain")
            with candidate_cols[3]:
                metric_card("Next gate", "DATA", "External PIT contract")
            st.warning("Remaining blockers: " + ", ".join(primary_state.get("remaining_blockers", [])))
            if primary_paths:
                st.caption(f"Primary research state: {primary_paths.get('state_path', '')}")
            if st.button("Create true-backtest spec and harness", type="secondary", width="stretch"):
                spec = build_portfolio_candidate_true_backtest_spec(primary_state)
                harness = build_portfolio_candidate_true_backtest_harness(spec)
                spec_paths = persist_portfolio_candidate_true_backtest_spec(spec, harness, root=REPO_ROOT)
                st.session_state["portfolio_lab_true_backtest_spec"] = {"spec": spec, "harness": harness, "paths": spec_paths}
                st.rerun()
        spec_state = st.session_state.get("portfolio_lab_true_backtest_spec")
        spec_path = (
            REPO_ROOT
            / "experiments/provider_aware_research/execution_outputs/PORTFOLIO-CANDIDATE-002-TRUE-BACKTEST-SPEC/PORTFOLIO-CANDIDATE-002-TRUE-BACKTEST-SPEC/true_backtest_spec.json"
        )
        harness_path = (
            REPO_ROOT
            / "experiments/provider_aware_research/execution_outputs/PORTFOLIO-CANDIDATE-002-TRUE-BACKTEST-SPEC/PORTFOLIO-CANDIDATE-002-TRUE-BACKTEST-SPEC/true_backtest_harness.json"
        )
        if spec_state is None and spec_path.exists() and harness_path.exists():
            spec_state = {
                "spec": json.loads(spec_path.read_text(encoding="utf-8")),
                "harness": json.loads(harness_path.read_text(encoding="utf-8")),
                "paths": {"spec_path": str(spec_path), "harness_path": str(harness_path)},
            }
        if spec_state:
            spec = spec_state.get("spec", {})
            harness = spec_state.get("harness", {})
            st.markdown("**True-backtest harness**")
            st.warning(
                f"{harness.get('status', 'UNKNOWN')}. The harness will not reuse proxy Workbench returns; "
                "it waits for a PIT/survivorship-free bundle before deriving trades from raw data."
            )
            harness_cols = st.columns(4)
            with harness_cols[0]:
                metric_card("Sleeves", len(spec.get("frozen_sleeves", [])), "Frozen, no tuning")
            with harness_cols[1]:
                metric_card("Required fields", len(spec.get("data_contract", {}).get("required_fields", [])), "Data contract")
            with harness_cols[2]:
                metric_card("Missing fields", len(harness.get("missing_data_contract_fields", [])), "Blocks execution")
            with harness_cols[3]:
                metric_card("Proxy reuse", "OFF", "No dry-run P&L")
            st.caption(f"Spec file: {spec_state.get('paths', {}).get('spec_path', '')}")
            if st.button("Attach mock admissible bundle", type="secondary", width="stretch"):
                bundle = build_portfolio_mock_admissible_data_bundle(spec)
                ready_harness = build_portfolio_candidate_true_backtest_harness(spec, data_bundle_manifest=bundle)
                skeleton = run_portfolio_candidate_true_backtest_skeleton(spec, ready_harness, bundle)
                bundle_paths = persist_portfolio_mock_admissible_data_bundle(bundle, skeleton, root=REPO_ROOT)
                st.session_state["portfolio_lab_mock_bundle_result"] = {
                    "bundle": bundle,
                    "harness": ready_harness,
                    "skeleton": skeleton,
                    "paths": bundle_paths,
                }
                st.rerun()
            if st.button("Attach manual partial bundle", type="secondary", width="stretch"):
                bundle = build_portfolio_manual_partial_data_bundle(spec)
                blocked_harness = build_portfolio_candidate_true_backtest_harness(spec, data_bundle_manifest=bundle)
                skeleton = run_portfolio_candidate_true_backtest_skeleton(spec, blocked_harness, bundle)
                bundle_paths = persist_portfolio_manual_partial_data_bundle(bundle, skeleton, root=REPO_ROOT)
                st.session_state["portfolio_lab_manual_partial_bundle_result"] = {
                    "bundle": bundle,
                    "harness": blocked_harness,
                    "skeleton": skeleton,
                    "paths": bundle_paths,
                }
                st.rerun()
        bundle_result = st.session_state.get("portfolio_lab_mock_bundle_result")
        if bundle_result:
            skeleton = bundle_result.get("skeleton", {})
            bundle = bundle_result.get("bundle", {})
            st.markdown("**Mock data-bundle plumbing**")
            st.info(
                f"{bundle.get('bundle_id', 'Mock bundle')} validates the harness shape only. "
                f"Runner state: {skeleton.get('status', 'UNKNOWN')}; no performance claim is allowed."
            )
            bundle_cols = st.columns(4)
            with bundle_cols[0]:
                metric_card("Covered fields", len(bundle.get("covered_fields", [])), "Contract fields")
            with bundle_cols[1]:
                metric_card("Harness", bundle_result.get("harness", {}).get("status", "UNKNOWN"), "Ready only in mock")
            with bundle_cols[2]:
                metric_card("Backtest", "NO", "No real run")
            with bundle_cols[3]:
                metric_card("Claim", "NO", "Synthetic bundle")
            st.caption(f"Mock bundle file: {bundle_result.get('paths', {}).get('bundle_path', '')}")
        manual_partial_result = st.session_state.get("portfolio_lab_manual_partial_bundle_result")
        if manual_partial_result:
            skeleton = manual_partial_result.get("skeleton", {})
            bundle = manual_partial_result.get("bundle", {})
            st.markdown("**Manual partial data path**")
            st.warning(
                f"{bundle.get('bundle_id', 'Manual partial bundle')} is exploratory-only. "
                f"Runner state: {skeleton.get('status', 'UNKNOWN')}; missing PIT/delisted fields keep the true backtest blocked."
            )
            partial_cols = st.columns(4)
            with partial_cols[0]:
                metric_card("Covered", len(bundle.get("covered_fields", [])), "Local/manual fields")
            with partial_cols[1]:
                metric_card("Missing", len(bundle.get("missing_fields_declared_upfront", [])), "Declared upfront")
            with partial_cols[2]:
                metric_card("Harness", manual_partial_result.get("harness", {}).get("status", "UNKNOWN"), "Blocked")
            with partial_cols[3]:
                metric_card("Claim", "NO", "Exploratory only")
            st.caption(f"Manual partial bundle file: {manual_partial_result.get('paths', {}).get('bundle_path', '')}")
        with st.expander("Open search controls and top candidates"):
            st.json(
                {
                    "selection_rule": search.get("selection_rule"),
                    "objective": search.get("objective"),
                    "overfit_controls": search.get("overfit_controls"),
                    "truncated": search.get("truncated"),
                    "exhaustive_within_search_pool": search.get("exhaustive_within_search_pool"),
                    "excluded_component_count": len(search.get("excluded_component_ids", [])),
                    "top_candidates": search.get("top_candidates", []),
                }
            )
    action_plan = preview.get("action_plan", [])
    if action_plan:
        st.markdown("**Recommended next actions**")
        for action in action_plan[:4]:
            severity = str(action.get("severity", "warn")).lower()
            message = f"**{action.get('title', 'Action')}**: {action.get('action', '')}"
            if severity == "block":
                st.error(message)
            elif severity == "pass":
                st.success(message)
            else:
                st.warning(message)
    auto_clean = preview.get("auto_clean", {})
    if auto_clean.get("available"):
        st.markdown("**Auto-clean basket**")
        st.caption("The lab removes highly correlated duplicates using a conservative rule: keep the stronger or less fragile component, never optimize hindsight weights.")
        st.info(auto_clean.get("summary", "Automatic de-duplication is available."))
        removed = pd.DataFrame(auto_clean.get("removed_components", []))
        if not removed.empty:
            st.dataframe(removed, width="stretch", hide_index=True)
        cleaned_ids = list(auto_clean.get("kept_component_ids", []))
        cleaned_preview = build_portfolio_lab_preview_from_components(
            components,
            cleaned_ids,
            policy=policy,
            max_component_weight=max_component_weight,
            max_rejected_weight=max_rejected_weight,
            max_convex_weight=max_convex_weight,
        )
        delta = float(cleaned_preview["summary"]["total_net_return"]) - float(summary["total_net_return"])
        clean_cols = st.columns(4)
        with clean_cols[0]:
            metric_card("Clean components", cleaned_preview["summary"]["component_count"], "After duplicate removal")
        with clean_cols[1]:
            metric_card("Clean net", f"{cleaned_preview['summary']['total_net_return']:.2f}", f"{delta:+.2f} vs current")
        with clean_cols[2]:
            metric_card("Clean drawdown", f"{cleaned_preview['summary']['max_drawdown']:.2f}", "After duplicate removal")
        with clean_cols[3]:
            metric_card("Clean decision", cleaned_preview["final_decision"]["decision"], "Still non-promotable")
        if cleaned_preview["final_decision"]["blockers"]:
            st.warning("Clean basket blockers: " + ", ".join(cleaned_preview["final_decision"]["blockers"]))
        else:
            st.success("Clean basket has no hard portfolio blocker, but promotion remains locked.")
    else:
        st.success("Auto-clean basket: no highly correlated duplicate removal suggested.")

    allocation = pd.DataFrame(preview["allocation"])
    equity = pd.DataFrame(preview["equity_curve"])
    contribution = pd.DataFrame(preview["contribution"])
    gates = pd.DataFrame(preview["gate_panel"])
    corr = pd.DataFrame(preview["correlation_matrix"])
    high_corr = pd.DataFrame(preview.get("high_correlation_pairs", []))

    section_note(
        "Read this block from left to right: first the portfolio path, then the pain, then which sleeves did the work, then whether the basket is secretly duplicated."
    )
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("**Portfolio equity**")
        st.caption("How to read it: a smoother line means components are offsetting each other; it is not a live-trading claim.")
        if not equity.empty:
            fig = px.line(equity, x="period", y="cumulative_net_return", markers=True)
            fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10), yaxis_title="Cumulative net")
            st.plotly_chart(fig, width="stretch")
    with chart_cols[1]:
        st.markdown("**Drawdown path**")
        st.caption("How to read it: this shows the local pain required to hold the basket through bad periods.")
        if not equity.empty:
            st.info(
                f"Context: max drawdown is {summary['max_drawdown']:.2f} additive return units "
                f"({summary['max_drawdown_pct']:.1f}% if one unit is read as 100%). "
                "Because Workbench dry-runs are proxy artifacts, use this as relative pain, not account P&L."
            )
            fig = px.area(equity, x="period", y="drawdown")
            fig.update_traces(line_color="#d12f5f", fillcolor="rgba(209,47,95,0.25)")
            fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10), yaxis_title="Drawdown")
            st.plotly_chart(fig, width="stretch")

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("**Contribution by component**")
        st.caption("How to read it: this shows the largest contributors only. If one bar dominates this view, the portfolio is still a disguised single bet.")
        if not contribution.empty:
            contribution = contribution.merge(allocation[["component_id", "strategy_name", "template", "sleeve"]], on="component_id", how="left")
            contribution["abs_contribution"] = contribution["contribution"].abs()
            contribution["component_label"] = contribution.apply(
                lambda row: compact_component_label(str(row["component_id"]), str(row.get("strategy_name", "")), str(row.get("template", ""))),
                axis=1,
            )
            contribution_view = contribution.sort_values("abs_contribution", ascending=False).head(24)
            hidden_count = max(0, len(contribution) - len(contribution_view))
            if hidden_count:
                st.info(f"Showing the top {len(contribution_view)} contributors by absolute impact. {hidden_count} small components are hidden to keep the chart readable.")
            fig = px.bar(
                contribution_view.sort_values("contribution"),
                x="contribution",
                y="component_label",
                orientation="h",
                color="sleeve",
                color_discrete_sequence=["#2563eb", "#0f9f75", "#f97316"],
                hover_data=["component_id", "template"],
            )
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Weighted contribution", yaxis_title="")
            st.plotly_chart(fig, width="stretch")
    with chart_cols[1]:
        st.markdown("**Correlation heatmap**")
        st.caption("How to read it: this is a focused heatmap of the highest-impact components, not the full 298-row matrix.")
        if not corr.empty:
            corr = corr.set_index("component_id")
            label_source = allocation.set_index("component_id") if not allocation.empty else pd.DataFrame()
            if not contribution.empty:
                heatmap_ids = contribution.sort_values("abs_contribution", ascending=False)["component_id"].astype(str).head(28).tolist()
            else:
                heatmap_ids = list(corr.index[:28])
            heatmap_ids = [component_id for component_id in heatmap_ids if component_id in corr.index]
            focused_corr = corr.loc[heatmap_ids, heatmap_ids] if heatmap_ids else corr.iloc[:0, :0]
            axis_labels = []
            for component_id in heatmap_ids:
                if component_id in label_source.index:
                    row = label_source.loc[component_id]
                    axis_labels.append(compact_component_label(component_id, str(row.get("strategy_name", component_id)), str(row.get("template", ""))))
                else:
                    axis_labels.append(component_id)
            if len(corr) > len(focused_corr):
                st.info(f"Showing {len(focused_corr)} highest-impact components out of {len(corr)}. Use the high-correlation table below for exact pairs.")
            fig = go.Figure(data=go.Heatmap(z=focused_corr.to_numpy(), x=axis_labels, y=axis_labels, colorscale="RdBu", zmin=-1, zmax=1))
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10), xaxis_tickangle=35)
            st.plotly_chart(fig, width="stretch")
            if high_corr.empty:
                st.success("No component pair crossed the high-correlation threshold. The basket is not obviously one duplicated bet.")
            else:
                first_pair = high_corr.iloc[0]
                st.warning(
                    f"{len(high_corr)} highly correlated pair(s) found. First action: remove either "
                    f"{first_pair['left_strategy']} or {first_pair['right_strategy']} and rerun."
                )
                st.dataframe(high_corr.head(30), width="stretch", hide_index=True)
                if len(high_corr) > 30:
                    st.caption(f"Showing first 30 of {len(high_corr)} high-correlation pairs.")

    st.markdown("**What-if removal**")
    st.caption("Remove one selected component and recompute the portfolio locally before changing the actual basket.")
    what_if_options = ["No removal"] + [row["component_id"] for row in preview["allocation"]]
    what_if_remove = st.selectbox(
        "Component to remove",
        what_if_options,
        format_func=lambda component_id: "No removal"
        if component_id == "No removal"
        else labels.get(component_id, component_id),
    )
    if what_if_remove != "No removal":
        active_ids = [row["component_id"] for row in preview["allocation"]]
        reduced_ids = [component_id for component_id in active_ids if component_id != what_if_remove]
        what_if = build_portfolio_lab_preview_from_components(
            components,
            reduced_ids,
            policy=policy,
            max_component_weight=max_component_weight,
            max_rejected_weight=max_rejected_weight,
            max_convex_weight=max_convex_weight,
        )
        delta = float(what_if["summary"]["total_net_return"]) - float(summary["total_net_return"])
        st.info(
            f"Without {labels.get(what_if_remove, what_if_remove)}: decision "
            f"{what_if['final_decision']['decision']}, net sum {what_if['summary']['total_net_return']:.2f} "
            f"({delta:+.2f} vs current), max drawdown {what_if['summary']['max_drawdown']:.2f}."
        )
        for action in what_if.get("action_plan", [])[:2]:
            st.caption(f"{action['title']}: {action['action']}")

    with st.expander("Open allocation table, gate panel, manifest, and final decision"):
        st.markdown("**Allocation table**")
        st.caption("Weights are explainable policy outputs, not optimized hindsight weights.")
        st.dataframe(allocation, width="stretch", hide_index=True)
        st.markdown("**Portfolio gates**")
        st.caption("PASS/WARN/BLOCK rows explain why the basket remains diagnostic-only or gets archived.")
        st.dataframe(gates, width="stretch", hide_index=True)
        st.markdown("**Portfolio manifest**")
        st.json(preview["portfolio_manifest"])
        st.markdown("**Final decision**")
        st.json(preview["final_decision"])

    if st.button("Persist portfolio diagnostic artifacts", type="primary"):
        paths = persist_portfolio_lab_preview(preview)
        st.success("Portfolio diagnostic artifacts written to the vault.")
        st.json(paths)


def sidebar_navigation(payload: dict[str, object], current_section: str) -> str:
    metrics = governance_metrics(payload)
    status = build_mission_status({**payload, "metrics": metrics})
    section_meta = mission_section_by_label(current_section)
    st.sidebar.markdown(
        mission_sidebar_html(section_meta.label, status),
        unsafe_allow_html=True,
    )
    selected_section = current_section if current_section in SECTIONS else SECTIONS[0]
    active_group = ""
    for section in MISSION_SECTIONS:
        if section.group != active_group:
            active_group = section.group
            st.sidebar.markdown(f'<div class="mc-nav-label">{active_group}</div>', unsafe_allow_html=True)
        button_type = "primary" if section.label == selected_section else "secondary"
        if st.sidebar.button(
            section.label,
            type=button_type,
            width="stretch",
            key=f"sidebar_nav_{section.label}",
            help=section.description,
        ):
            selected_section = section.label
        st.sidebar.caption(section.description)
    return selected_section


def main() -> None:
    inject_theme()
    payload = load_dashboard_payload(Path("."))
    if "active_section" not in st.session_state:
        st.session_state["active_section"] = "Mission Brief"
    sidebar_section = sidebar_navigation(payload, st.session_state["active_section"])
    if sidebar_section != st.session_state["active_section"]:
        st.session_state["active_section"] = sidebar_section
    section = st.session_state["active_section"] if st.session_state["active_section"] in SECTIONS else "Mission Brief"
    st.session_state["active_section"] = section

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


if __name__ == "__main__":
    main()
