"""Portfolio Studio - il laboratorio visuale del trading lab.

Sito nuovo, costruito attorno a un flusso unico:
  1. ARENA    - testa e confronta tutte le strategie del catalogo;
  2. REGIMI   - guarda quale famiglia e' ammessa in ogni regime di mercato;
  3. COMPOSER - per ogni regime il basket migliore, composti in un portfolio
                regime-switching confrontato con la baseline statica.

Tutto e' diagnostico su dati proxy: nessuna promozione, nessun live claim.
Avvio:  streamlit run dashboard/studio.py   (porta 8502 da .streamlit/config.toml)
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.lab_dashboard_data import (  # noqa: E402
    build_strategy_factory_components,
    load_dashboard_payload,
    load_portfolio_lab_components,
)
from src.experiments.honest_baselines_trial import (  # noqa: E402
    HonestBaselinesConfig,
    run_honest_baselines_trial,
)
from src.experiments.regime_portfolio_studio import (  # noqa: E402
    component_strategy_family,
    run_regime_studio,
)
from src.experiments.workbench_portfolio_engine import (  # noqa: E402
    _aggregate_curve,
    _component_return_series,
)

st.set_page_config(page_title="Portfolio Studio", page_icon=":crystal_ball:", layout="wide", initial_sidebar_state="collapsed")

REGIME_COLORS = {
    "TREND_UP_LOW_VOL": "#2dd4a7",
    "TREND_UP_HIGH_VOL": "#a3e635",
    "RANGE_NORMAL": "#5b8cff",
    "TREND_DOWN_OR_CHOP": "#f5a623",
    "DRAWDOWN_STRESS": "#fb7185",
    "INSUFFICIENT_HISTORY": "#64748b",
}
REGIME_LABELS_IT = {
    "TREND_UP_LOW_VOL": "Trend up, vol bassa",
    "TREND_UP_HIGH_VOL": "Trend up, vol alta",
    "RANGE_NORMAL": "Range normale",
    "TREND_DOWN_OR_CHOP": "Trend down / chop",
    "DRAWDOWN_STRESS": "Stress / drawdown",
    "INSUFFICIENT_HISTORY": "Storia insufficiente",
}
POSTURE_BADGE = {
    "ALLOW_PROXY": ("ALLOW", "go"),
    "REDUCE": ("REDUCE", "hold"),
    "RISK_OVERLAY": ("OVERLAY", "plum"),
    "OBSERVE_ONLY": ("OBSERVE", "mute"),
    "BLOCK": ("BLOCK", "cut"),
}
FAMILY_GLYPH = {
    "Momentum": "[MO]",
    "Mean Reversion": "[MR]",
    "Event Catalyst": "[EV]",
    "Regime Risk Engine": "[RR]",
    "Dollar-Bar Microstructure": "[DB]",
    "9:30 AM ORB": "[OR]",
}

SECTIONS = ["Home", "Strategy Arena", "Regimi", "Composer"]


# ---------------------------------------------------------------------------
# theme
# ---------------------------------------------------------------------------

def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
        :root {
          --bg: #070b14;
          --panel: rgba(17,24,40,.72);
          --panel-solid: #101727;
          --line: rgba(120,140,180,.16);
          --ink: #e9eef8;
          --ink-soft: #b9c3d6;
          --muted: #7e8aa3;
          --accent: #5b8cff;
          --accent-2: #8b5cf6;
          --good: #2dd4a7;
          --warn: #f5a623;
          --bad: #fb7185;
          --plum: #a78bfa;
        }
        [data-testid="stHeader"], #MainMenu, footer { display:none !important; }
        section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display:none !important; }
        html, body, [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(1200px 600px at 80% -15%, rgba(91,140,255,.14), transparent 55%),
            radial-gradient(900px 480px at 5% 0%, rgba(139,92,246,.10), transparent 50%),
            radial-gradient(700px 380px at 50% 110%, rgba(45,212,167,.06), transparent 55%),
            var(--bg);
          color: var(--ink);
          font-family: 'Space Grotesk', system-ui, sans-serif;
        }
        .block-container { padding-top: 1.2rem; padding-bottom: 5rem; max-width: 1340px; }
        code, .mono { font-family: 'JetBrains Mono', monospace; }

        /* nav */
        .studio-nav {
          display:flex; align-items:center; gap:14px;
          background: var(--panel);
          border: 1px solid var(--line);
          backdrop-filter: blur(14px);
          border-radius: 16px; padding: 12px 18px; margin-bottom: 14px;
        }
        .studio-logo { font-weight:700; font-size:17px; letter-spacing:-.01em; }
        .studio-logo b { background: linear-gradient(90deg,#5b8cff,#8b5cf6,#2dd4a7); -webkit-background-clip:text; background-clip:text; color:transparent; }
        .studio-tag { font-size:10.5px; color:var(--muted); text-transform:uppercase; letter-spacing:.14em; }

        .stButton > button {
          background: transparent; color: var(--ink-soft);
          border: 1px solid var(--line); border-radius: 10px;
          font-family:'Space Grotesk'; font-weight:600; font-size:13.5px;
          transition: all .15s ease;
        }
        .stButton > button:hover { color:#fff; border-color: rgba(91,140,255,.6); box-shadow: 0 0 14px rgba(91,140,255,.18); }
        .stButton > button[kind="primary"] {
          background: linear-gradient(135deg,#5b8cff 0%,#8b5cf6 100%);
          border: none; color:#fff;
          box-shadow: 0 4px 24px rgba(91,140,255,.35);
        }
        .stButton > button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 6px 28px rgba(139,92,246,.45); }

        /* hero */
        @keyframes floatGlow { 0%,100% { opacity:.75 } 50% { opacity:1 } }
        .hero {
          position:relative; overflow:hidden;
          border-radius: 22px; border: 1px solid var(--line);
          background:
            radial-gradient(620px 300px at 85% -30%, rgba(91,140,255,.22), transparent 60%),
            radial-gradient(480px 260px at 12% 120%, rgba(45,212,167,.12), transparent 55%),
            linear-gradient(160deg, rgba(20,28,48,.95), rgba(10,14,26,.98));
          padding: 54px 56px 46px; margin-bottom: 18px;
        }
        .hero-kicker { color: var(--accent); font-size: 12px; letter-spacing:.22em; text-transform:uppercase; font-weight:700; animation: floatGlow 4s ease-in-out infinite; }
        .hero h1 {
          font-size: 46px; line-height:1.06; letter-spacing:-.03em; margin: 14px 0 14px; font-weight:700;
        }
        .hero h1 span { background: linear-gradient(90deg,#5b8cff 0%,#8b5cf6 45%,#2dd4a7 100%); -webkit-background-clip:text; background-clip:text; color: transparent; }
        .hero p { color: var(--ink-soft); font-size: 16.5px; max-width: 720px; line-height: 1.6; margin:0; }
        .hero .disclaimer { margin-top: 18px; display:inline-block; font-size: 11.5px; color: var(--warn); border:1px solid rgba(245,166,35,.35); background: rgba(245,166,35,.08); padding: 6px 12px; border-radius: 999px; letter-spacing:.04em; }

        /* glass cards */
        .tile {
          background: var(--panel); border: 1px solid var(--line);
          backdrop-filter: blur(12px);
          border-radius: 16px; padding: 18px 20px; height: 100%;
          transition: border-color .2s ease;
        }
        .tile:hover { border-color: rgba(91,140,255,.45); }
        .tile .k { color: var(--muted); font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; }
        .tile .v { font-family:'JetBrains Mono'; font-size: 27px; font-weight: 700; margin-top: 6px; letter-spacing:-.02em; }
        .tile .v.pos { color: var(--good); } .tile .v.neg { color: var(--bad); }
        .tile .n { color: var(--muted); font-size: 12px; margin-top: 6px; line-height:1.45; }

        .step-grid { display:grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin: 6px 0 4px; }
        .step {
          border:1px solid var(--line); border-radius:16px; padding:20px;
          background: linear-gradient(180deg, rgba(20,28,48,.65), rgba(12,17,30,.65));
        }
        .step .num { font-family:'JetBrains Mono'; color: var(--accent); font-size: 13px; font-weight:700; }
        .step .t { font-weight:700; font-size: 16.5px; margin: 8px 0 6px; }
        .step .d { color: var(--muted); font-size: 13px; line-height: 1.55; }

        .badge { display:inline-block; padding: 3px 11px; border-radius: 999px; font-size: 10.5px; font-weight:700; letter-spacing:.08em; text-transform: uppercase; border: 1px solid; }
        .badge.go { color: var(--good); border-color: rgba(45,212,167,.4); background: rgba(45,212,167,.08); }
        .badge.cut { color: var(--bad); border-color: rgba(251,113,133,.4); background: rgba(251,113,133,.08); }
        .badge.hold { color: var(--warn); border-color: rgba(245,166,35,.4); background: rgba(245,166,35,.08); }
        .badge.mute { color: var(--muted); border-color: var(--line); background: rgba(120,140,180,.07); }
        .badge.plum { color: var(--plum); border-color: rgba(167,139,250,.4); background: rgba(167,139,250,.08); }
        .badge.blue { color: var(--accent); border-color: rgba(91,140,255,.4); background: rgba(91,140,255,.08); }

        .regime-chip { display:inline-flex; align-items:center; gap:8px; padding: 7px 14px; border-radius: 12px; border:1px solid var(--line); background: rgba(12,17,30,.6); font-size: 13px; font-weight:600; }
        .regime-dot { width:9px; height:9px; border-radius:50%; display:inline-block; }

        .section-title { font-size: 24px; font-weight: 700; letter-spacing: -.02em; margin: 4px 0 2px; }
        .section-sub { color: var(--muted); font-size: 13.5px; margin-bottom: 12px; }

        [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius: 12px; overflow:hidden; }
        [data-testid="stExpander"] details { background: var(--panel); border:1px solid var(--line) !important; border-radius: 14px !important; }
        .stPlotlyChart { background: var(--panel); border:1px solid var(--line); border-radius: 16px; padding: 10px; }
        .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label { color: var(--ink-soft) !important; font-size: 13px !important; }
        .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
        .stTabs [data-baseweb="tab"] { color: var(--muted); }
        .stTabs [aria-selected="true"] { color: var(--accent) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def fmt_net(value: object, mode: str, *, signed: bool = True) -> str:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "n/d"
    if not math.isfinite(number):
        return "n/d"
    if str(mode) == "compounded":
        if abs(number) > 100:
            return "fuori scala"
        prefix = "+" if signed and number > 0 else ""
        return f"{prefix}{number * 100:.1f}%"
    if abs(number) > 1e9:
        return "fuori scala (riavvia il server)"
    return f"{number:+.2f} u" if signed else f"{number:.2f} u"


def tone_of(value: object) -> str:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number) or number == 0:
        return ""
    return "pos" if number > 0 else "neg"


def tile(label: str, value: str, note: str, tone: str = "") -> None:
    st.markdown(
        f'<div class="tile"><div class="k">{label}</div><div class="v {tone}">{value}</div><div class="n">{note}</div></div>',
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, *, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=24, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#b9c3d6", size=12),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(gridcolor="rgba(120,140,180,.12)")
    fig.update_yaxes(gridcolor="rgba(120,140,180,.12)")
    return fig


# ---------------------------------------------------------------------------
# cached data layer
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carico il catalogo strategie...")
def load_catalog(saved_limit: int, factory_variants: int) -> list[dict]:
    saved = load_portfolio_lab_components(limit=saved_limit)
    factory = build_strategy_factory_components(max_variants=factory_variants) if factory_variants else []
    return [*saved, *factory]


@st.cache_data(show_spinner="Carico router e regime map...")
def load_market_context() -> dict:
    payload = load_dashboard_payload(Path("."))
    router = payload.get("strategy_regime_router", {})
    matrix = router.get("matrix") if isinstance(router, dict) else None
    regime_map = payload.get("regime_map")
    current = payload.get("current_market_regime", {})
    return {
        "router_matrix": matrix if isinstance(matrix, pd.DataFrame) else pd.DataFrame(),
        "regime_map": regime_map if isinstance(regime_map, pd.DataFrame) else pd.DataFrame(),
        "current_regime": current if isinstance(current, dict) else {},
    }


@st.cache_data(show_spinner="Ottimizzo i basket per ogni regime... (la prima volta richiede qualche minuto)")
def run_studio_cached(saved_limit: int, factory_variants: int, policy: str) -> dict:
    catalog = load_catalog(saved_limit, factory_variants)
    context = load_market_context()
    return run_regime_studio(catalog, context["router_matrix"], context["regime_map"], policy=policy)


@st.cache_data(show_spinner="Calcolo baseline oneste e permutation test... (prima volta ~1 min)")
def honest_baselines_cached(saved_limit: int, factory_variants: int) -> dict:
    catalog = load_catalog(saved_limit, factory_variants)
    context = load_market_context()
    return run_honest_baselines_trial(
        catalog, context["router_matrix"], context["regime_map"], HonestBaselinesConfig()
    )


@st.cache_data(show_spinner=False)
def strategy_table(saved_limit: int, factory_variants: int) -> pd.DataFrame:
    rows = []
    for component in load_catalog(saved_limit, factory_variants):
        series = _component_return_series(component)
        curve, mode = _aggregate_curve(series)
        rows.append(
            {
                "id": str(component.get("component_id")),
                "Strategia": str(component.get("strategy_name")),
                "Famiglia": component_strategy_family(component),
                "Fonte": str(component.get("source", "saved_workbench")).replace("_", " "),
                "Trade": int(component.get("trade_count") or 0),
                "Net": float(curve.iloc[-1]) if len(curve) else 0.0,
                "Modo": mode,
                "Decisione": str(component.get("decision", "")).replace("_", " "),
                "Warning": len(component.get("bias_warnings", []) or []),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def strategy_curve(saved_limit: int, factory_variants: int, component_id: str) -> pd.DataFrame:
    for component in load_catalog(saved_limit, factory_variants):
        if str(component.get("component_id")) == component_id:
            series = _component_return_series(component)
            curve, mode = _aggregate_curve(series)
            return pd.DataFrame({"period": [str(p) for p in curve.index], "value": curve.to_numpy(), "mode": mode})
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# navigation
# ---------------------------------------------------------------------------

def navigation() -> str:
    if "studio_section" not in st.session_state:
        st.session_state["studio_section"] = "Home"
    cols = st.columns([2.4, 1, 1.4, 1, 1.3, 2.6])
    with cols[0]:
        st.markdown(
            '<div class="studio-logo"><b>Portfolio Studio</b></div><div class="studio-tag">Adaptive Equity Trading Lab</div>',
            unsafe_allow_html=True,
        )
    for column, section in zip(cols[1:5], SECTIONS):
        with column:
            kind = "primary" if st.session_state["studio_section"] == section else "secondary"
            if st.button(section, key=f"nav_{section}", type=kind, width="stretch"):
                st.session_state["studio_section"] = section
                st.rerun()
    with cols[5]:
        current = load_market_context()["current_regime"]
        label = str(current.get("regime_label", "n/d"))
        color = REGIME_COLORS.get(label, "#64748b")
        st.markdown(
            f'<div class="regime-chip" style="float:right"><span class="regime-dot" style="background:{color}"></span>'
            f'Regime: {REGIME_LABELS_IT.get(label, label)}</div>',
            unsafe_allow_html=True,
        )
    return str(st.session_state["studio_section"])


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def page_home(saved_limit: int, factory_variants: int) -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">Regime-aware portfolio engine</div>
          <h1>Ogni regime di mercato ha il suo <span>portfolio migliore</span>.<br>Qui lo trovi, lo vedi, lo componi.</h1>
          <p>
            Lo Studio testa l'intero catalogo di strategie, chiede al regime router quali famiglie sono ammesse
            in ogni stato del mercato, trova il basket migliore per ciascun regime e li compone in un unico
            portfolio che cambia pelle quando cambia il mercato.
          </p>
          <div class="disclaimer">DATI PROXY - DIAGNOSTICA - NESSUNA PROMOZIONE / LIVE TRADING</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    table = strategy_table(saved_limit, factory_variants)
    context = load_market_context()
    regimes = context["router_matrix"]["regime_label"].nunique() if not context["router_matrix"].empty else 0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tile("Strategie in catalogo", f"{len(table)}", "Workbench salvate + factory generate")
    with c2:
        tile("Famiglie strategiche", f"{table['Famiglia'].nunique() if not table.empty else 0}", "Momentum, mean reversion, eventi, regime...")
    with c3:
        tile("Regimi mappati", f"{regimes}", "Stati di mercato dal regime router")
    with c4:
        positive = int((table["Net"] > 0).sum()) if not table.empty else 0
        tile("Strategie positive", f"{positive}/{len(table)}", "Sul path locale proxy - non e' una promessa", tone="pos" if positive else "")
    st.markdown(
        """
        <div class="step-grid">
          <div class="step"><div class="num">01</div><div class="t">Strategy Arena</div>
            <div class="d">Tutte le strategie a confronto: filtra per famiglia, ordina per net, apri la curva di ognuna.</div></div>
          <div class="step"><div class="num">02</div><div class="t">Regimi</div>
            <div class="d">La matrice Strategia x Regime: chi e' ammesso, chi e' ridotto, chi e' bloccato quando il mercato cambia stato.</div></div>
          <div class="step"><div class="num">03</div><div class="t">Composer</div>
            <div class="d">Il basket migliore per ogni regime, composti in un portfolio dinamico confrontato con la baseline statica.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cta1, cta2, _ = st.columns([1.2, 1.2, 3])
    with cta1:
        if st.button("Apri la Strategy Arena", type="primary", width="stretch"):
            st.session_state["studio_section"] = "Strategy Arena"
            st.rerun()
    with cta2:
        if st.button("Componi il portfolio", width="stretch"):
            st.session_state["studio_section"] = "Composer"
            st.rerun()


def page_arena(saved_limit: int, factory_variants: int) -> None:
    st.markdown('<div class="section-title">Strategy Arena</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Tutto il catalogo, testato sugli stream locali. Ordina, filtra, apri la curva. "u" = unita\' additive proxy, non percentuali.</div>', unsafe_allow_html=True)
    table = strategy_table(saved_limit, factory_variants)
    if table.empty:
        st.warning("Nessuna strategia in catalogo. Crea dry-run nel Workbench o abilita la factory.")
        return
    f1, f2, f3 = st.columns([1.4, 1.4, 1.2])
    with f1:
        families = st.multiselect("Famiglia", sorted(table["Famiglia"].unique()), default=[])
    with f2:
        sources = st.multiselect("Fonte", sorted(table["Fonte"].unique()), default=[])
    with f3:
        order = st.selectbox("Ordina per", ["Net (desc)", "Net (asc)", "Trade (desc)", "Warning (asc)"])
    view = table.copy()
    if families:
        view = view[view["Famiglia"].isin(families)]
    if sources:
        view = view[view["Fonte"].isin(sources)]
    by, asc = {"Net (desc)": ("Net", False), "Net (asc)": ("Net", True), "Trade (desc)": ("Trade", False), "Warning (asc)": ("Warning", True)}[order]
    view = view.sort_values(by, ascending=asc).reset_index(drop=True)

    k1, k2, k3 = st.columns(3)
    mode_overall = "compounded" if (view["Modo"] == "compounded").all() else "additive"
    with k1:
        tile("Strategie filtrate", f"{len(view)}", "Nel set corrente")
    with k2:
        best_value = view["Net"].max() if not view.empty else 0.0
        tile("Migliore", fmt_net(best_value, mode_overall), str(view.iloc[0]["Strategia"])[:42] if not view.empty else "-", tone=tone_of(best_value))
    with k3:
        med = view["Net"].median() if not view.empty else 0.0
        tile("Mediana", fmt_net(med, mode_overall), "Meta' del catalogo fa peggio di cosi'", tone=tone_of(med))

    show = view.copy()
    show["Net"] = [fmt_net(v, m) for v, m in zip(view["Net"], view["Modo"])]
    st.dataframe(show.drop(columns=["id", "Modo"]), width="stretch", hide_index=True, height=420)

    st.markdown("##### Apri una strategia")
    labels = {row["id"]: f'{row["Strategia"]}  ·  {row["Famiglia"]}  ·  {fmt_net(row["Net"], row["Modo"])}' for _, row in view.iterrows()}
    if not labels:
        return
    chosen = st.selectbox("Strategia", list(labels), format_func=lambda key: labels[key])
    curve = strategy_curve(saved_limit, factory_variants, chosen)
    if curve.empty:
        st.info("Nessuno stream disponibile per questa strategia.")
        return
    row = view[view["id"] == chosen].iloc[0]
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        tile("Net", fmt_net(row["Net"], row["Modo"]), "Fine del path locale", tone=tone_of(row["Net"]))
    with d2:
        tile("Trade", f'{row["Trade"]}', "Campione del dry-run")
    with d3:
        tile("Famiglia", FAMILY_GLYPH.get(row["Famiglia"], ""), row["Famiglia"])
    with d4:
        tile("Bias warning", f'{row["Warning"]}', row["Decisione"] or "diagnostic")
    fig = go.Figure(go.Scatter(x=curve["period"], y=curve["value"], mode="lines", line=dict(color="#5b8cff", width=2.4), fill="tozeroy", fillcolor="rgba(91,140,255,.10)", name="curva"))
    st.plotly_chart(chart_layout(fig, height=320), width="stretch")
    st.caption("Curva locale proxy. Sotto N~100 trade nessun risultato distingue edge da fortuna (vedi power curve PCTRL).")


def page_regimes(saved_limit: int, factory_variants: int) -> None:
    st.markdown('<div class="section-title">Strategia x Regime</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Il router decide chi gioca in ogni stato del mercato. ALLOW gioca, REDUCE gioca a meta\' size, OVERLAY governa il rischio, BLOCK sta fuori.</div>', unsafe_allow_html=True)
    context = load_market_context()
    matrix = context["router_matrix"]
    if matrix.empty:
        st.warning("Router matrix non disponibile.")
        return
    regimes = sorted(matrix["regime_label"].astype(str).unique())
    families = sorted(matrix["strategy_family"].astype(str).unique())
    posture_of = {(str(r["regime_label"]), str(r["strategy_family"])): str(r["posture"]) for _, r in matrix.iterrows()}
    header = "".join(
        f'<th style="padding:8px 10px;text-align:left"><span class="regime-chip"><span class="regime-dot" style="background:{REGIME_COLORS.get(regime, "#64748b")}"></span>{REGIME_LABELS_IT.get(regime, regime)}</span></th>'
        for regime in regimes
    )
    body = ""
    for family in families:
        cells = ""
        for regime in regimes:
            text, css = POSTURE_BADGE.get(posture_of.get((regime, family), "OBSERVE_ONLY"), ("OBSERVE", "mute"))
            cells += f'<td style="padding:8px 10px"><span class="badge {css}">{text}</span></td>'
        body += f'<tr><td style="padding:8px 10px;font-weight:600">{FAMILY_GLYPH.get(family, "")} {family}</td>{cells}</tr>'
    st.markdown(
        f'<div class="tile" style="overflow-x:auto"><table style="border-collapse:separate;border-spacing:2px;width:100%"><tr><th></th>{header}</tr>{body}</table></div>',
        unsafe_allow_html=True,
    )
    st.caption("La matrice viene dall'evidenza archiviata del lab: e' governance difensiva, non alpha dimostrato.")

    st.markdown("##### Il basket migliore per ogni regime")
    st.caption("Ricerca governata sui soli componenti ammessi in quel regime. La prima esecuzione richiede qualche minuto, poi resta in cache.")
    if st.button("Calcola i basket per regime", type="primary"):
        st.session_state["studio_baskets_ready"] = True
    if st.session_state.get("studio_baskets_ready"):
        studio = run_studio_cached(saved_limit, factory_variants, "equal_weight")
        baskets = studio.get("baskets_by_regime", {})
        columns = st.columns(3)
        for index, regime in enumerate(regimes):
            basket = baskets.get(regime, {})
            summary = basket.get("summary", {}) or {}
            mode = str(summary.get("aggregation_mode", "additive"))
            net = summary.get("total_net_return_compounded", summary.get("total_net_return", 0.0))
            with columns[index % 3]:
                color = REGIME_COLORS.get(regime, "#64748b")
                st.markdown(
                    f"""
                    <div class="tile" style="border-top:3px solid {color}; margin-bottom:12px">
                      <div class="k">{REGIME_LABELS_IT.get(regime, regime)}</div>
                      <div class="v {tone_of(net)}">{fmt_net(net, mode)}</div>
                      <div class="n">{len(basket.get("basket_component_ids", []))} componenti nel basket ·
                      ammessi {basket.get("allowed_count", 0)} / bloccati {basket.get("blocked_count", 0)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def page_composer(saved_limit: int, factory_variants: int) -> None:
    st.markdown('<div class="section-title">Portfolio Composer</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Un portfolio che cambia basket quando il mercato cambia regime, confrontato con la baseline statica equal-weight. Diagnostica proxy: non promuovibile.</div>', unsafe_allow_html=True)
    policy = st.radio("Pesi dentro ogni basket", ["equal_weight", "inverse_volatility", "sleeve_allocation"], horizontal=True)
    if st.button("Componi il portfolio regime-switching", type="primary"):
        st.session_state["studio_composed"] = policy
    chosen_policy = st.session_state.get("studio_composed")
    if not chosen_policy:
        st.info("Premi il bottone: lo Studio ottimizza un basket per ogni regime e li compone nel tempo. La prima volta serve qualche minuto.")
        return
    studio = run_studio_cached(saved_limit, factory_variants, str(chosen_policy))
    composition = studio.get("composition", {})
    summary = composition.get("summary", {}) or {}
    if not summary:
        st.warning("Composizione non disponibile: servono stream con date reali.")
        return
    mode = str(summary.get("aggregation_mode", "additive"))
    honest = honest_baselines_cached(saved_limit, factory_variants)
    hr = honest.get("results", {})
    perm = honest.get("permutation", {})
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tile("Dynamic", fmt_net(summary.get("dynamic_total"), mode), "Portfolio regime-switching", tone=tone_of(summary.get("dynamic_total")))
    with c2:
        tile(
            "Static onesta",
            fmt_net(hr.get("static_cost_matched"), "compounded"),
            "Equal-weight solo componenti a costi reali (<=100bps), dedup",
            tone=tone_of(hr.get("static_cost_matched")),
        )
    with c3:
        tile(
            "Top-5 senza routing",
            fmt_net(hr.get("unconditional_top5"), "compounded"),
            "Selezione semplice, nessun regime switching",
            tone=tone_of(hr.get("unconditional_top5")),
        )
    with c4:
        tile("Max DD dynamic", fmt_net(summary.get("dynamic_max_drawdown"), mode, signed=False), f"Static onesta vs legacy: la legacy ({fmt_net(hr.get('static_all_legacy'), 'compounded')}) e' gonfiata dai cost tier", tone=tone_of(summary.get("dynamic_max_drawdown")))
    p_value = perm.get("p_value")
    if p_value is not None:
        if float(p_value) <= 0.05:
            st.success(f"Permutation test ({perm.get('n', 0)} shift delle label di regime): p = {p_value}. Il TIMING di regime e' statisticamente supportato su questo campione.")
        else:
            st.warning(
                f"Permutation test ({perm.get('n', 0)} shift delle label di regime): p = {p_value}. "
                "Il valore viene dalla SELEZIONE dei componenti, non dal timing di regime "
                "(verdetto TRIAL-STUDIO-OOS-008, audit 2026-06-11). La vecchia baseline 'static' era gonfiata dai cost tier."
            )

    curves = composition.get("curves")
    if isinstance(curves, pd.DataFrame) and not curves.empty:
        fig = go.Figure()
        # bande di regime sullo sfondo
        segment_start = 0
        rows = curves.reset_index(drop=True)
        for i in range(1, len(rows) + 1):
            if i == len(rows) or rows.loc[i, "regime"] != rows.loc[segment_start, "regime"]:
                regime = rows.loc[segment_start, "regime"]
                fig.add_vrect(
                    x0=rows.loc[segment_start, "period"], x1=rows.loc[min(i, len(rows) - 1), "period"],
                    fillcolor=REGIME_COLORS.get(str(regime), "#64748b"), opacity=0.06, line_width=0,
                )
                segment_start = i
        fig.add_trace(go.Scatter(x=rows["period"], y=rows["static"], name="Static", mode="lines", line=dict(color="#7e8aa3", width=1.8, dash="dot")))
        fig.add_trace(go.Scatter(x=rows["period"], y=rows["dynamic"], name="Dynamic", mode="lines", line=dict(color="#2dd4a7", width=2.6)))
        st.plotly_chart(chart_layout(fig, height=430), width="stretch")
        legend = "  ".join(
            f'<span class="regime-chip" style="margin-right:6px"><span class="regime-dot" style="background:{REGIME_COLORS.get(r, "#64748b")}"></span>{REGIME_LABELS_IT.get(r, r)}</span>'
            for r in rows["regime"].unique()
        )
        st.markdown(legend, unsafe_allow_html=True)

    usage = composition.get("regime_usage")
    baskets = studio.get("baskets_by_regime", {})
    u1, u2 = st.columns([1.1, 1.6])
    with u1:
        if isinstance(usage, pd.DataFrame) and not usage.empty:
            fig = go.Figure(go.Bar(
                x=usage["periods"], y=[REGIME_LABELS_IT.get(r, r) for r in usage["regime"]],
                orientation="h", marker=dict(color=[REGIME_COLORS.get(str(r), "#64748b") for r in usage["regime"]]),
            ))
            fig.update_layout(title="Periodi per regime")
            st.plotly_chart(chart_layout(fig, height=300), width="stretch")
    with u2:
        st.markdown("**I basket scelti, regime per regime**")
        table = strategy_table(saved_limit, factory_variants)
        name_of = dict(zip(table["id"], table["Strategia"])) if not table.empty else {}
        for regime, basket in baskets.items():
            ids = basket.get("basket_component_ids", [])
            with st.expander(f"{REGIME_LABELS_IT.get(regime, regime)} - {len(ids)} componenti"):
                for component_id in ids[:12]:
                    weight = basket.get("weights", {}).get(component_id, 0.0)
                    st.markdown(f'- `{component_id[:18]}` {name_of.get(component_id, "")} — peso {weight:.0%}')
                if len(ids) > 12:
                    st.caption(f"...e altri {len(ids) - 12}")

    delta = float(summary.get("dynamic_vs_static_delta", 0.0) or 0.0)
    if delta > 0:
        st.success(f"Su questo path locale il regime switching AGGIUNGE {fmt_net(delta, mode)} rispetto alla baseline statica. Resta un diagnostico proxy: serve il true data gate prima di qualsiasi claim.")
    else:
        st.warning(f"Su questo path locale il regime switching TOGLIE {fmt_net(abs(delta), mode)} rispetto alla baseline statica: le regole regime sono governance difensiva, non return enhancement dimostrato.")
    st.caption("Sample proxy, strategie sopravvissute a selezione, stream additivi: questo numero non autorizza nessuna decisione di capitale reale.")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    inject_theme()
    with st.expander("Impostazioni catalogo", expanded=False):
        s1, s2 = st.columns(2)
        with s1:
            saved_limit = st.slider("Workbench salvate (max)", 10, 60, 60, 10)
        with s2:
            factory_variants = st.slider("Varianti factory generate", 0, 96, 48, 12)
    section = navigation()
    if section == "Home":
        page_home(saved_limit, factory_variants)
    elif section == "Strategy Arena":
        page_arena(saved_limit, factory_variants)
    elif section == "Regimi":
        page_regimes(saved_limit, factory_variants)
    else:
        page_composer(saved_limit, factory_variants)


if __name__ == "__main__":
    main()
