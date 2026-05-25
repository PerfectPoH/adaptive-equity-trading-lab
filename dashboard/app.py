from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    governance_metrics,
    load_dashboard_payload,
    project_capability_rows,
    strategy_detail,
    strategy_rows,
)


st.set_page_config(page_title="Adaptive Equity Trading Lab", layout="wide")


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
        :root {
          --lab-bg: #f8fafc;
          --lab-panel: #ffffff;
          --lab-ink: #1e293b;
          --lab-muted: #64748b;
          --lab-blue: #2563eb;
          --lab-blue-soft: #dbeafe;
          --lab-amber: #f97316;
          --lab-line: #d8dee6;
          --lab-red: #dc2626;
          --lab-green: #16a34a;
        }
        html, body, [data-testid="stAppViewContainer"] {
          background: var(--lab-bg);
          color: var(--lab-ink);
          font-family: "Fira Sans", system-ui, sans-serif;
        }
        h1, h2, h3 { letter-spacing: 0; }
        .block-container { padding-top: 1.5rem; max-width: 1480px; }
        .lab-hero {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background:
            linear-gradient(135deg, rgba(37, 99, 235, .10), rgba(249, 115, 22, .08)),
            #ffffff;
          padding: 28px 30px;
          margin-bottom: 18px;
        }
        .lab-kicker {
          font-family: "Fira Code", monospace;
          color: var(--lab-blue);
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: .06em;
        }
        .lab-title {
          font-size: clamp(34px, 5vw, 64px);
          line-height: 1.02;
          font-weight: 700;
          margin: 10px 0 12px;
          color: #0f172a;
        }
        .lab-subtitle {
          max-width: 960px;
          color: var(--lab-muted);
          font-size: 18px;
          line-height: 1.55;
        }
        .metric-card, .strategy-card, .lab-section {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          background: var(--lab-panel);
          padding: 16px;
        }
        .metric-label {
          color: var(--lab-muted);
          font-family: "Fira Code", monospace;
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 600;
        }
        .metric-value {
          color: #0f172a;
          font-size: 30px;
          font-weight: 700;
          margin-top: 4px;
          overflow-wrap: anywhere;
          line-height: 1.2;
        }
        .metric-value-long {
          font-size: 22px;
        }
        .metric-note { color: var(--lab-muted); font-size: 13px; margin-top: 4px; }
        .status-pill {
          display: inline-block;
          border-radius: 999px;
          padding: 4px 10px;
          font-family: "Fira Code", monospace;
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
        .strategy-title { font-size: 22px; font-weight: 700; margin: 6px 0; }
        .strategy-family {
          font-family: "Fira Code", monospace;
          color: var(--lab-muted);
          font-size: 12px;
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
          border-left: 4px solid var(--lab-red);
          background: #fef2f2;
          color: #7f1d1d;
        }
        .flow-node {
          border: 1px solid var(--lab-line);
          border-radius: 6px;
          padding: 10px;
          background: #ffffff;
          font-family: "Fira Code", monospace;
          font-size: 12px;
          min-height: 54px;
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
        .small-muted { color: var(--lab-muted); font-size: 13px; }
        div[data-testid="stMetric"] {
          border: 1px solid var(--lab-line);
          border-radius: 8px;
          padding: 12px;
          background: #fff;
        }
        @media (max-width: 768px) {
          .lab-hero { padding: 20px; }
          .lab-title { font-size: 38px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    css = status.replace(" ", "-")
    return f'<span class="status-pill status-{css}">{status}</span>'


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
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers+text",
            marker=dict(size=30, color=["#2563eb"] + ["#3b82f6"] * (len(nodes) - 2) + ["#f97316"], line=dict(color="#ffffff", width=2)),
            text=[f"{i + 1}" for i in range(len(nodes))],
            textfont=dict(color="white", size=12, family="Fira Code"),
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
            width=125,
        )
    fig.update_layout(
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
        height=max(220, 52 * len(frame)),
        margin=dict(l=10, r=20, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        xaxis_title="Runs",
        yaxis_title="",
        font=dict(family="Fira Sans", color="#1e293b"),
    )
    return fig


def render_hero(metrics: dict[str, object]) -> None:
    st.markdown(
        f"""
        <div class="lab-hero">
          <div class="lab-kicker">Adaptive Equity Trading Lab / Final Research Console</div>
          <div class="lab-title">A quant lab that learned to say no.</div>
          <div class="lab-subtitle">
            This dashboard is the forensic cockpit for the research program: every strategy, blocker,
            data source, cost gate, governance rule, and final decision is surfaced as an auditable product UI.
            The current state is <strong>{metrics["final_policy"]}</strong>, not capital deployment.
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
          <strong>Current operating conclusion:</strong> small-cap/free-data directional alpha is paused.
          Primary blockers: {", ".join(blockers) if blockers else "none recorded"}.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_strategy_atlas(payload: dict[str, object]) -> None:
    ledger = payload["ledger"]
    rows = strategy_rows(ledger)
    st.header("Strategy Atlas")
    st.caption("Each strategy has a thesis, execution logic, graph demonstration, and the actual archived verdicts from the lab.")

    status_counts = rows.groupby("status", as_index=False).size().rename(columns={"size": "count"})
    status_fig = px.pie(status_counts, names="status", values="count", hole=0.58, color="status", color_discrete_map={
        "ARCHIVED": "#f97316",
        "BLOCKED": "#dc2626",
        "DIAGNOSTIC": "#2563eb",
        "NOT RUN": "#64748b",
        "PROMOTED": "#16a34a",
    })
    status_fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), font=dict(family="Fira Sans"))
    left, right = st.columns([1, 2])
    with left:
        st.plotly_chart(status_fig, width="stretch")
    with right:
        st.dataframe(rows[["name", "family", "runs", "status", "primary_decision"]], width="stretch", hide_index=True)

    for profile in STRATEGY_PROFILES:
        detail = strategy_detail(profile.key, ledger)
        runs = detail["runs"]
        st.markdown("---")
        header_l, header_r = st.columns([3, 1])
        with header_l:
            st.markdown(f'<div class="strategy-family">{profile.family}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="strategy-title">{profile.name}</div>', unsafe_allow_html=True)
        with header_r:
            st.markdown(status_badge(str(detail["status"])), unsafe_allow_html=True)

        a, b = st.columns([1.2, 1])
        with a:
            st.markdown("**How it works**")
            st.write(profile.mechanism)
            st.markdown("**Why it mattered**")
            st.write(profile.thesis)
            if not runs.empty:
                st.dataframe(runs[["run_id", "decision", "provider_query_performed", "backtest_performed", "promotion_allowed"]], width="stretch", hide_index=True)
        with b:
            st.plotly_chart(strategy_result_chart(runs), width="stretch")

        st.markdown("**Strategy graph demonstration**")
        st.plotly_chart(flow_chart(detail["flow_nodes"]), width="stretch")


def render_results_and_data(payload: dict[str, object]) -> None:
    st.header("Results And Data Dashboard")
    ledger = payload["ledger"]
    regime_map = payload["regime_map"]
    allocation = payload["allocation"]
    smallcap = payload["smallcap_microstructure"]
    data_matrix = payload["data_matrix"]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Decision Ledger")
        st.dataframe(ledger, width="stretch", hide_index=True)
    with c2:
        if not ledger.empty:
            counts = ledger.groupby("decision", as_index=False).size().sort_values("size", ascending=False).head(12)
            fig = px.bar(counts, x="size", y="decision", orientation="h", color="size", color_continuous_scale=["#dbeafe", "#2563eb"])
            fig.update_layout(height=520, margin=dict(l=0, r=10, t=10, b=10), coloraxis_showscale=False, yaxis_title="", xaxis_title="Count")
            st.plotly_chart(fig, width="stretch")

    st.subheader("Regime Map")
    if not regime_map.empty and "regime_label" in regime_map.columns:
        regime_counts = regime_map.groupby("regime_label", as_index=False).size()
        fig = px.bar(regime_counts, x="regime_label", y="size", color="regime_label", color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=10), showlegend=False, xaxis_title="", yaxis_title="Symbol-days")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(regime_map.tail(500), width="stretch", hide_index=True)

    st.subheader("Portfolio And Microstructure Diagnostics")
    m1, m2 = st.columns(2)
    with m1:
        if not allocation.empty and {"symbol", "diagnostic_weight"}.issubset(allocation.columns):
            fig = px.bar(allocation.sort_values("diagnostic_weight", ascending=False), x="symbol", y="diagnostic_weight", color="realized_volatility", color_continuous_scale="Blues")
            fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=10), xaxis_title="", yaxis_title="Diagnostic weight")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(allocation, width="stretch", hide_index=True)
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
            fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=10), xaxis_title="Median dollar volume", yaxis_title="Spread proxy")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(smallcap, width="stretch", hide_index=True)

    st.subheader("Data Upgrade Matrix")
    st.dataframe(data_matrix, width="stretch", hide_index=True)


def render_lab_explainer(payload: dict[str, object]) -> None:
    st.header("How The Laboratory Works")
    st.markdown(
        """
        <div class="callout">
        The project is not a simple backtester. It is a falsification machine: every idea must pass data quality,
        timestamp integrity, cost realism, sample-size, robustness, and governance gates before it can become a candidate.
        </div>
        """,
        unsafe_allow_html=True,
    )
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

    capabilities = project_capability_rows()
    st.markdown('<div class="capability-grid">', unsafe_allow_html=True)
    for row in capabilities.to_dict("records"):
        st.markdown(
            f"""
            <div class="capability">
              <div class="strategy-family">{row["area"]} / {row["state"]}</div>
              <div style="font-weight:700;margin:8px 0;">{row["capability"]}</div>
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
        "The next phase can be a user-facing strategy workbench: users define a rule, choose data assumptions, run the same governance gates, "
        "and inspect results without bypassing PIT, cost, robustness, or promotion controls. This dashboard intentionally stops before that."
    )


def main() -> None:
    inject_theme()
    payload = load_dashboard_payload(Path("."))

    tabs = st.tabs(["Overview", "Strategies", "Results & Data", "Project Anatomy"])
    with tabs[0]:
        render_overview(payload)
    with tabs[1]:
        render_strategy_atlas(payload)
    with tabs[2]:
        render_results_and_data(payload)
    with tabs[3]:
        render_lab_explainer(payload)


if __name__ == "__main__":
    main()
