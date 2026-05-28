from __future__ import annotations

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
    build_workbench_data_scope_preview,
    build_workbench_flow_nodes,
    build_workbench_manifest,
    build_workbench_pre_run_gate,
    build_workbench_backtest_readiness,
    build_workbench_comparison_table,
    delisted_data_source_gate_payload,
    governance_metrics,
    load_dashboard_payload,
    persist_workbench_run_bundle,
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
    display_safe_records,
    load_workbench_strategy_cards,
)


st.set_page_config(page_title="Adaptive Equity Trading Lab", layout="wide", initial_sidebar_state="expanded")

SECTIONS = ["Command Center", "Strategies", "Results & Data", "Project Anatomy", "Strategy Workbench"]
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
          color: var(--lab-ink);
          font-family: "Instrument Sans", system-ui, sans-serif;
        }
        section[data-testid="stSidebar"] {
          background: rgba(251, 250, 247, .94);
          border-right: 1px solid var(--lab-line);
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
          border: 0;
          border-bottom: 1px solid transparent;
          border-radius: 8px;
          margin-bottom: 8px;
          padding: 8px 10px;
          background: transparent;
        }
        h1, h2, h3 {
          font-family: "Instrument Sans", system-ui, sans-serif;
          letter-spacing: -.025em;
          color: var(--lab-strong);
        }
        .block-container {
          padding-top: 1.25rem;
          padding-bottom: 5rem;
          max-width: 1500px;
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
          padding: 12px 14px;
          margin-bottom: 24px;
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
        }
        div[data-testid="stButton"] > button[kind="primary"] {
          background: #2563eb;
          color: #ffffff;
          border-color: #2563eb;
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
          padding-top: 26px;
          margin-top: 42px;
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
    selected = current_section if current_section in SECTIONS else "Command Center"
    columns = st.columns([1.15, 0.9, 1.05, 1.05, 1.25])
    for column, section_name in zip(columns, SECTIONS):
        with column:
            button_type = "primary" if section_name == selected else "secondary"
            st.button(section_name, type=button_type, width="stretch", key=f"main_nav_{section_name}", on_click=set_active_section, args=(section_name,))
    return st.session_state.get("active_section", selected)


def set_active_section(section_name: str) -> None:
    st.session_state["active_section"] = section_name


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
    marker_colors = {"buy": "#1f5eff", "exit": "#d97706", "block": "#d12f5f"}
    marker_symbols = {"buy": "triangle-up", "exit": "circle", "block": "x"}
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
    st.caption("One section per strategy: real price chart, signal anatomy, explanation, process graph, and audit trail.")

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


def render_results_and_data(payload: dict[str, object]) -> None:
    st.header("Results And Data Dashboard")
    ledger = payload["ledger"]
    regime_map = payload["regime_map"]
    allocation = payload["allocation"]
    smallcap = payload["smallcap_microstructure"]
    data_matrix = payload["data_matrix"]
    orb = payload.get("orb_930", {})

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Ledger Rows", len(ledger), "Final decisions and probes")
    with c2:
        metric_card("Regime Rows", len(regime_map), "Large-cap/ETF symbol-days mapped")
    with c3:
        metric_card("Data Upgrades", len(data_matrix), "Provider paths scored")

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
    gate_cols = st.columns([1.25, 1])
    with gate_cols[0]:
        matrix = delisted_gate["candidate_source_matrix"]
        if not matrix.empty:
            st.dataframe(matrix[["provider", "delisted_symbols", "survivorship_free_prices", "pit_membership", "gate_status", "notes"]], width="stretch", hide_index=True)
    with gate_cols[1]:
        requirements = delisted_gate["unlock_requirements"]
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
            trade_rows = pd.DataFrame(preview.get("trade_rows", []))
            equity_curve = pd.DataFrame(preview.get("equity_curve", []))
            if not trade_rows.empty:
                st.markdown("**Generated local trade list**")
                st.dataframe(trade_rows, width="stretch", hide_index=True)
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
            with st.expander("Open Markdown dry-run report"):
                st.code(preview.get("markdown_report", ""), language="markdown")
            with st.expander("Open exportable strategy blueprint"):
                st.json(build_workbench_strategy_blueprint(manifest, preview))
            artifact_bundle = st.session_state.get("workbench_artifact_bundle")
            if artifact_bundle:
                st.markdown("**Persisted artifacts**")
                st.json(artifact_bundle)

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


def sidebar_navigation(payload: dict[str, object], current_section: str) -> str:
    metrics = governance_metrics(payload)
    st.sidebar.markdown("### Adaptive Lab")
    st.sidebar.caption("Research console")
    section = st.sidebar.radio(
        "Navigate",
        SECTIONS,
        index=SECTIONS.index(current_section) if current_section in SECTIONS else 0,
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div class="sidebar-tile">
          <div class="sidebar-label">Promoted</div>
          <div class="sidebar-value">{metrics["promoted_strategy_count"]}</div>
          <div class="sidebar-note">No strategy passed promotion gates.</div>
        </div>
        <div style="height:10px;"></div>
        <div class="sidebar-tile">
          <div class="sidebar-label">Final mode</div>
          <div class="sidebar-value" style="font-size:20px;">{metrics["final_policy"]}</div>
          <div class="sidebar-note">Research posture after closure.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Navigation is in the sidebar so the Streamlit header cannot cover section controls.")
    return section


def main() -> None:
    inject_theme()
    payload = load_dashboard_payload(Path("."))
    if "active_section" not in st.session_state:
        st.session_state["active_section"] = "Command Center"
    sidebar_section = sidebar_navigation(payload, st.session_state["active_section"])
    if sidebar_section != st.session_state["active_section"]:
        st.session_state["active_section"] = sidebar_section
    section = main_navigation(st.session_state["active_section"])
    st.session_state["active_section"] = section
    shell_nav(section)

    if section == "Command Center":
        render_overview(payload)
    elif section == "Strategies":
        render_strategy_atlas(payload)
    elif section == "Results & Data":
        render_results_and_data(payload)
    elif section == "Project Anatomy":
        render_lab_explainer(payload)
    else:
        render_strategy_workbench()


if __name__ == "__main__":
    main()
