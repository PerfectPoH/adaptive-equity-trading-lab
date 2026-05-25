from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    WORKBENCH_TEMPLATES,
    build_strategy_chart_story,
    build_workbench_manifest,
    governance_metrics,
    load_dashboard_payload,
    project_capability_rows,
    project_lifecycle_rows,
    strategy_detail,
    strategy_rows,
)


st.set_page_config(page_title="Adaptive Equity Trading Lab", layout="wide", initial_sidebar_state="expanded")

SECTIONS = ["Command Center", "Strategies", "Results & Data", "Project Anatomy", "Strategy Workbench"]


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo:wght@500;600;700;800&family=Roboto+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');
        :root {
          --lab-bg: #f8fafc;
          --lab-panel: #ffffff;
          --lab-ink: #1e293b;
          --lab-strong: #0f172a;
          --lab-muted: #64748b;
          --lab-blue: #2563eb;
          --lab-blue-2: #3b82f6;
          --lab-amber: #f97316;
          --lab-line: #d8dee6;
          --lab-red: #dc2626;
          --lab-green: #16a34a;
          --lab-slate: #111827;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {
          display: none !important;
          visibility: hidden !important;
        }
        html, body, [data-testid="stAppViewContainer"] {
          background: var(--lab-bg);
          color: var(--lab-ink);
          font-family: "Inter", system-ui, sans-serif;
        }
        section[data-testid="stSidebar"] {
          background: #0b1220;
          border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] * {
          color: #e5edf8;
        }
        section[data-testid="stSidebar"] .sidebar-tile {
          border: 1px solid #22304a;
          border-radius: 8px;
          background: #111827;
          padding: 14px;
          min-height: 108px;
        }
        section[data-testid="stSidebar"] .sidebar-label {
          color: #93c5fd !important;
          font-family: "Roboto Mono", monospace;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
        }
        section[data-testid="stSidebar"] .sidebar-value {
          color: #ffffff !important;
          font-family: "Exo", system-ui, sans-serif;
          font-size: 30px;
          font-weight: 800;
          line-height: 1.05;
          overflow-wrap: anywhere;
        }
        section[data-testid="stSidebar"] .sidebar-note {
          color: #cbd5e1 !important;
          font-size: 13px;
          line-height: 1.35;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label {
          border: 1px solid #22304a;
          border-radius: 8px;
          margin-bottom: 8px;
          padding: 8px 10px;
          background: rgba(255, 255, 255, .04);
        }
        h1, h2, h3 {
          font-family: "Exo", system-ui, sans-serif;
          letter-spacing: 0;
          color: var(--lab-strong);
        }
        .block-container {
          padding-top: .75rem;
          padding-bottom: 3rem;
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
          border-radius: 8px;
          background: rgba(255, 255, 255, .92);
          backdrop-filter: blur(12px);
          padding: 10px 12px;
          margin-bottom: 16px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, .06);
        }
        .main-nav-card {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: #ffffff;
          padding: 10px 12px 2px;
          margin-bottom: 20px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
        }
        .main-nav-card [role="radiogroup"] {
          gap: 8px;
          flex-wrap: wrap;
        }
        .main-nav-card [role="radiogroup"] label {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          padding: 8px 12px;
          background: #f8fafc;
        }
        .main-nav-card [role="radiogroup"] label:has(input:checked) {
          border-color: #93c5fd;
          background: #eff6ff;
        }
        .lab-brand {
          font-family: "Roboto Mono", monospace;
          font-size: 12px;
          font-weight: 700;
          color: var(--lab-blue);
          text-transform: uppercase;
        }
        .lab-nav-state {
          font-family: "Roboto Mono", monospace;
          font-size: 12px;
          color: var(--lab-muted);
        }
        .lab-hero {
          position: relative;
          overflow: hidden;
          border: 1px solid #1e293b;
          border-radius: 8px;
          background:
            linear-gradient(115deg, rgba(37, 99, 235, .98), rgba(15, 23, 42, .98) 52%, rgba(249, 115, 22, .88)),
            #0f172a;
          padding: 34px 34px 28px;
          margin-bottom: 18px;
          color: #f8fafc;
          min-height: 300px;
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
          font-family: "Roboto Mono", monospace;
          color: #bfdbfe;
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: .06em;
        }
        .lab-title {
          position: relative;
          z-index: 1;
          font-family: "Exo", system-ui, sans-serif;
          font-size: clamp(42px, 6vw, 78px);
          line-height: .98;
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
          border-radius: 8px;
          background: var(--lab-panel);
          padding: 16px;
          box-shadow: 0 12px 34px rgba(15, 23, 42, .055);
        }
        .metric-label, .strategy-family, .eyebrow {
          color: var(--lab-muted);
          font-family: "Roboto Mono", monospace;
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: .04em;
        }
        .metric-value {
          color: var(--lab-strong);
          font-family: "Exo", system-ui, sans-serif;
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
          font-family: "Roboto Mono", monospace;
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
          border-radius: 8px;
          background:
            linear-gradient(180deg, rgba(248,250,252,.96), rgba(255,255,255,.98)),
            #ffffff;
          padding: 22px;
          margin: 22px 0;
          box-shadow: 0 18px 46px rgba(15, 23, 42, .065);
        }
        .strategy-title {
          font-family: "Exo", system-ui, sans-serif;
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
          border-left: 4px solid var(--lab-blue);
          background: #eff6ff;
          padding: 12px 14px;
          border-radius: 6px;
          color: #1e3a8a;
          margin: 12px 0;
        }
        .danger-callout {
          border-left-color: var(--lab-red);
          background: #fef2f2;
          color: #7f1d1d;
        }
        .compact-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
          gap: 12px;
        }
        .mini-tile {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: #fff;
          padding: 12px;
          min-height: 96px;
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
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    css = status.replace(" ", "-")
    return f'<span class="status-pill status-{css}">{status}</span>'


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
    st.markdown('<div class="main-nav-card">', unsafe_allow_html=True)
    selected = st.radio(
        "Primary navigation",
        SECTIONS,
        index=SECTIONS.index(current_section) if current_section in SECTIONS else 0,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return selected


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
    colors = ["#2563eb"] + ["#3b82f6"] * max(len(nodes) - 2, 0) + ["#f97316"]
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers+text",
            marker=dict(size=30, color=colors[: len(nodes)], line=dict(color="#ffffff", width=2)),
            text=[f"{i + 1}" for i in range(len(nodes))],
            textfont=dict(color="white", size=12, family="Roboto Mono"),
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
            font=dict(size=11, color="#1e293b"),
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
        color_continuous_scale=["#dbeafe", "#2563eb"],
        text="count",
    )
    fig.update_layout(
        template="plotly_white",
        height=max(220, 52 * len(frame)),
        margin=dict(l=10, r=20, t=20, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        coloraxis_showscale=False,
        xaxis_title="Runs",
        yaxis_title="",
        font=dict(family="Inter", color="#1e293b"),
        xaxis=dict(tickfont=dict(color="#475569"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
        yaxis=dict(tickfont=dict(color="#334155"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
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
            increasing_line_color="#16a34a",
            decreasing_line_color="#dc2626",
            increasing_fillcolor="rgba(22,163,74,.65)",
            decreasing_fillcolor="rgba(220,38,38,.65)",
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
            marker=dict(color="rgba(37,99,235,.18)"),
            hovertemplate="Volume %{customdata:,}<extra></extra>",
            customdata=prices["volume"],
        )
    )
    marker_colors = {"buy": "#16a34a", "exit": "#2563eb", "block": "#dc2626"}
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
                textfont=dict(size=11, color=color, family="Roboto Mono"),
                name=str(marker["label"]),
                hovertemplate="%{text}<br>%{x}<br>$%{y:.2f}<extra></extra>",
            )
        )
    fig.update_layout(
        template="plotly_white",
        title=dict(text=str(story["title"]), font=dict(size=16, family="Exo", color="#0f172a")),
        height=430,
        margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter", color="#1e293b"),
        xaxis=dict(rangeslider=dict(visible=False), showgrid=True, gridcolor="#e2e8f0"),
        yaxis=dict(title="", showgrid=True, gridcolor="#e2e8f0", tickfont=dict(color="#475569")),
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
              <div style="font-family:Exo,system-ui,sans-serif;font-weight:800;font-size:18px;margin:6px 0;">{row["name"]}</div>
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
                "ARCHIVED": "#f97316",
                "BLOCKED": "#dc2626",
                "DIAGNOSTIC": "#2563eb",
                "NOT RUN": "#64748b",
                "PROMOTED": "#16a34a",
            },
        )
        status_fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), font=dict(family="Inter"))
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

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Ledger Rows", len(ledger), "Final decisions and probes")
    with c2:
        metric_card("Regime Rows", len(regime_map), "Large-cap/ETF symbol-days mapped")
    with c3:
        metric_card("Data Upgrades", len(data_matrix), "Provider paths scored")

    st.markdown('<div class="results-spacer"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if not ledger.empty:
            counts = ledger.groupby("decision", as_index=False).size().sort_values("size", ascending=False).head(12)
            fig = px.bar(counts, x="size", y="decision", orientation="h", color="size", color_continuous_scale=["#dbeafe", "#2563eb"])
            fig.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=0, r=10, t=10, b=10),
                coloraxis_showscale=False,
                yaxis_title="",
                xaxis_title="Count",
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                font=dict(color="#1e293b"),
                xaxis=dict(tickfont=dict(color="#475569"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
                yaxis=dict(tickfont=dict(color="#334155"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
            )
            st.plotly_chart(fig, width="stretch")
    with c2:
        if not regime_map.empty and "regime_label" in regime_map.columns:
            regime_counts = regime_map.groupby("regime_label", as_index=False).size()
            fig = px.bar(regime_counts, x="regime_label", y="size", color="regime_label", color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=0, r=0, t=10, b=10),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Symbol-days",
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                font=dict(color="#1e293b"),
                xaxis=dict(tickfont=dict(color="#334155"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
                yaxis=dict(tickfont=dict(color="#475569"), title_font=dict(color="#64748b"), gridcolor="#e2e8f0"),
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
    st.header("Strategy Workbench")
    st.markdown(
        """
        <div class="callout">
        This is the first step of the next phase: a user-facing strategy builder. For now it creates a governed
        strategy manifest and explains the data/gate contract before any backtest or provider query can run.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Strategy Draft")
        name = st.text_input("Strategy name", value="My falsifiable strategy")
        template = st.selectbox("Strategy template", list(WORKBENCH_TEMPLATES.keys()))
        universe = st.selectbox(
            "Universe",
            [
                "large-cap / ETF clean-data sandbox",
                "small-cap active-only exploratory sandbox",
                "local archived Databento panel",
                "custom universe pending PIT validation",
            ],
        )
        holding_period = st.slider("Holding period days", min_value=1, max_value=180, value=21)
        cost_bps = st.slider("Round-trip cost model (bps)", min_value=0, max_value=1000, value=500, step=25)
        provider_query = st.checkbox("Allow external provider query after pre-run gate", value=False)
    with right:
        st.subheader("Governance Preview")
        manifest = build_workbench_manifest(
            name=name,
            template=template,
            universe=universe,
            holding_period_days=holding_period,
            cost_bps=cost_bps,
            allow_provider_query=provider_query,
        )
        st.json(manifest)

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
