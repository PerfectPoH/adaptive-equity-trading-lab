"""Portfolio Studio - il laboratorio visuale del trading lab.

Sito costruito attorno a un flusso unico:
  1. ARENA    - testa e confronta tutte le strategie del catalogo;
  2. REGIMI   - guarda quale famiglia e' ammessa in ogni regime di mercato;
  3. COMPOSER - per ogni regime il basket migliore, composti in un portfolio
                regime-switching confrontato con la baseline statica;
  4. METODO   - la storia del lab e le regole anti-bias.

Estetica: carta/inchiostro di abedbarakat.me, stile report di ricerca.
Lingue: IT / EN (toggle in navigazione).
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

st.set_page_config(
    page_title="Portfolio Studio — Adaptive Equity Trading Lab",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# palette: colori accento del portfolio abedbarakat.me
# ---------------------------------------------------------------------------

INK = "#3b3b3b"
MUTED = "#6f6f6f"
ACCENT = "#2f7d62"

REGIME_COLORS = {
    "TREND_UP_LOW_VOL": "#2f7d62",
    "TREND_UP_HIGH_VOL": "#7a9a3d",
    "RANGE_NORMAL": "#3b6ea5",
    "TREND_DOWN_OR_CHOP": "#c0922b",
    "DRAWDOWN_STRESS": "#b5462f",
    "INSUFFICIENT_HISTORY": "#8a877f",
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

SECTIONS = ["home", "arena", "regimes", "composer", "method"]

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

REGIME_LABELS = {
    "it": {
        "TREND_UP_LOW_VOL": "Trend up, vol bassa",
        "TREND_UP_HIGH_VOL": "Trend up, vol alta",
        "RANGE_NORMAL": "Range normale",
        "TREND_DOWN_OR_CHOP": "Trend down / chop",
        "DRAWDOWN_STRESS": "Stress / drawdown",
        "INSUFFICIENT_HISTORY": "Storia insufficiente",
    },
    "en": {
        "TREND_UP_LOW_VOL": "Trend up, low vol",
        "TREND_UP_HIGH_VOL": "Trend up, high vol",
        "RANGE_NORMAL": "Normal range",
        "TREND_DOWN_OR_CHOP": "Trend down / chop",
        "DRAWDOWN_STRESS": "Stress / drawdown",
        "INSUFFICIENT_HISTORY": "Insufficient history",
    },
}

T = {
    "it": {
        "nav.home": "Home", "nav.arena": "Arena", "nav.regimes": "Regimi",
        "nav.composer": "Composer", "nav.method": "Metodo", "nav.regime": "Regime",
        "settings": "Impostazioni catalogo",
        "settings.saved": "Workbench salvate (max)", "settings.factory": "Varianti factory generate",
        "na": "n/d", "offscale": "fuori scala", "offscale.restart": "fuori scala (riavvia il server)",
        "hero.kicker": "Adaptive Equity Trading Lab — ricerca quantitativa governata",
        "hero.h1": 'Ogni regime di mercato ha il suo <span>portfolio migliore</span>.<br>Qui lo trovi, lo vedi, lo componi.',
        "hero.p": ("Questo laboratorio non vende una strategia vincente: costruisce un processo che non bara. "
                   "Lo Studio testa l'intero catalogo di strategie, chiede al regime router quali famiglie sono ammesse "
                   "in ogni stato del mercato, trova il basket migliore per ciascun regime e li compone in un unico "
                   "portfolio che cambia pelle quando cambia il mercato."),
        "hero.disc": "Dati proxy · diagnostica · nessuna promozione / live trading",
        "engine.lbl": "Come funziona l'engine",
        "engine.nodes": ["Dati & snapshot", "Data gates", "Esperimenti preregistrati",
                         "DSR & multiplicity budget", "Regime router", "Basket per regime", "Portfolio Composer"],
        "engine.p1": ("Ogni idea entra come <b>trial preregistrato</b>: ipotesi, metrica primaria e criteri di successo "
                      "dichiarati prima di vedere i risultati. I gate statistici — Deflated Sharpe Ratio, permutation test, "
                      "budget di molteplicità — decidono cosa sopravvive. Il <b>regime router</b> stabilisce quali famiglie "
                      "di strategie possono giocare in ogni stato del mercato, e il <b>Composer</b> le assembla in un "
                      "portfolio regime-switching confrontato con baseline oneste."),
        "engine.p2": ("Il risultato più importante finora non è una strategia redditizia: è un sistema che "
                      "<b>rifiuta ripetutamente di promuovere prove deboli</b>. La storia completa è nella pagina Metodo."),
        "tiles.catalog": "Strategie in catalogo", "tiles.catalog.n": "Workbench salvate + factory generate",
        "tiles.families": "Famiglie strategiche", "tiles.families.n": "Momentum, mean reversion, eventi, regime...",
        "tiles.regimes": "Regimi mappati", "tiles.regimes.n": "Stati di mercato dal regime router",
        "tiles.positive": "Strategie positive", "tiles.positive.n": "Sul path locale proxy — non è una promessa",
        "steps.1n": "01 — TESTA", "steps.1t": "Strategy Arena",
        "steps.1d": "Tutte le strategie a confronto: filtra per famiglia, ordina per net, apri la curva di ognuna e leggi i suoi bias warning.",
        "steps.2n": "02 — GOVERNA", "steps.2t": "Regimi",
        "steps.2d": "La matrice Strategia × Regime: chi è ammesso, chi gioca a metà size, chi resta fuori quando il mercato cambia stato.",
        "steps.3n": "03 — COMPONI", "steps.3t": "Composer",
        "steps.3d": "Il basket migliore per ogni regime, composti in un portfolio dinamico confrontato con baseline oneste e permutation test.",
        "cta.arena": "Apri la Strategy Arena", "cta.composer": "Componi il portfolio",
        "arena.title": "Strategy Arena",
        "arena.sub": 'Tutto il catalogo, testato sugli stream locali. Ordina, filtra, apri la curva. "u" = unità additive proxy, non percentuali.',
        "arena.empty": "Nessuna strategia in catalogo. Crea dry-run nel Workbench o abilita la factory.",
        "arena.f.family": "Famiglia", "arena.f.source": "Fonte", "arena.f.order": "Ordina per",
        "arena.o.netdesc": "Net (disc.)", "arena.o.netasc": "Net (cresc.)", "arena.o.trades": "Trade (disc.)", "arena.o.warn": "Warning (cresc.)",
        "arena.k.filtered": "Strategie filtrate", "arena.k.filtered.n": "Nel set corrente",
        "arena.k.best": "Migliore", "arena.k.median": "Mediana", "arena.k.median.n": "Metà del catalogo fa peggio di così",
        "arena.open": "Apri una strategia", "arena.select": "Strategia",
        "arena.nostream": "Nessuno stream disponibile per questa strategia.",
        "arena.d.net": "Net", "arena.d.net.n": "Fine del path locale", "arena.d.trades": "Trade",
        "arena.d.trades.n": "Campione del dry-run", "arena.d.family": "Famiglia", "arena.d.warn": "Bias warning",
        "arena.caption": "Curva locale proxy. Sotto N~100 trade nessun risultato distingue edge da fortuna (vedi power curve PCTRL).",
        "col.name": "Strategia", "col.family": "Famiglia", "col.source": "Fonte", "col.trades": "Trade",
        "col.net": "Net", "col.decision": "Decisione", "col.warnings": "Warning",
        "reg.title": "Strategia × Regime",
        "reg.sub": "Il router decide chi gioca in ogni stato del mercato. ALLOW gioca, REDUCE gioca a metà size, OVERLAY governa il rischio, BLOCK sta fuori.",
        "reg.warn": "Router matrix non disponibile.",
        "reg.caption": "La matrice viene dall'evidenza archiviata del lab: è governance difensiva, non alpha dimostrato.",
        "reg.baskets": "Il basket migliore per ogni regime",
        "reg.baskets.caption": "Ricerca governata sui soli componenti ammessi in quel regime. La prima esecuzione richiede qualche minuto, poi resta in cache.",
        "reg.baskets.btn": "Calcola i basket per regime",
        "reg.basket.meta": "componenti nel basket · ammessi {a} / bloccati {b}",
        "comp.title": "Portfolio Composer",
        "comp.sub": "Un portfolio che cambia basket quando il mercato cambia regime, confrontato con la baseline statica equal-weight. Diagnostica proxy: non promuovibile.",
        "comp.weights": "Pesi dentro ogni basket",
        "comp.btn": "Componi il portfolio regime-switching",
        "comp.info": "Premi il bottone: lo Studio ottimizza un basket per ogni regime e li compone nel tempo. La prima volta serve qualche minuto.",
        "comp.warn": "Composizione non disponibile: servono stream con date reali.",
        "comp.dynamic": "Dynamic", "comp.dynamic.n": "Portfolio regime-switching",
        "comp.static": "Static onesta", "comp.static.n": "Equal-weight solo componenti a costi reali (<=100bps), dedup",
        "comp.top5": "Top-5 senza routing", "comp.top5.n": "Selezione semplice, nessun regime switching",
        "comp.dd": "Max DD dynamic",
        "comp.dd.n": "Static onesta vs legacy: la legacy ({v}) è gonfiata dai cost tier",
        "comp.perm.ok": "Permutation test ({n} shift delle label di regime): p = {p}. Il TIMING di regime è statisticamente supportato su questo campione.",
        "comp.perm.warn": ("Permutation test ({n} shift delle label di regime): p = {p}. Il valore viene dalla SELEZIONE dei componenti, "
                           "non dal timing di regime (verdetto TRIAL-STUDIO-OOS-008, audit 2026-06-11). La vecchia baseline 'static' era gonfiata dai cost tier."),
        "comp.usage": "Periodi per regime",
        "comp.baskets": "I basket scelti, regime per regime",
        "comp.components": "componenti", "comp.weight": "peso", "comp.others": "...e altri {n}",
        "comp.delta.pos": "Su questo path locale il regime switching AGGIUNGE {v} rispetto alla baseline statica. Resta un diagnostico proxy: serve il true data gate prima di qualsiasi claim.",
        "comp.delta.neg": "Su questo path locale il regime switching TOGLIE {v} rispetto alla baseline statica: le regole regime sono governance difensiva, non return enhancement dimostrato.",
        "comp.caption": "Sample proxy, strategie sopravvissute a selezione, stream additivi: questo numero non autorizza nessuna decisione di capitale reale.",
        "met.title": "Metodo & garanzie",
        "met.sub": "Le regole che ogni esperimento deve rispettare prima che un numero venga preso sul serio. Sono cablate nel codice, non scritte su un post-it.",
        "met.story.lbl": "La storia, in breve",
        "met.story.p1": ("Il lab nasce come pipeline ML large-cap. Quando il backtest non ha battuto il buy-and-hold, "
                         "il fallimento è stato documentato e la baseline <b>declassata a controllo negativo</b> invece che ritoccata "
                         'finché non "funzionasse". La track small-cap successiva ha prodotto un edge apparente da +169%: '
                         "l'audit del sizing lo ha smontato, riclassificandolo come <b>artefatto di leva e path</b> — archiviato, non promosso."),
        "met.story.p2": ("Oggi il lab gira in modalità <b>risk &amp; regime engine</b>: zero strategie promosse, una regola di portfolio "
                         "preregistrata e <b>congelata</b> (2026-06-11), replica out-of-sample schedulata ogni primo del mese senza "
                         "possibilità di modifica. Il valore misurato finora viene dalla <b>selezione dei componenti</b>, "
                         "non dal timing di regime: lo dice il permutation test, e la pagina Composer lo mostra senza trucchi."),
        "met.rules.lbl": "Le otto regole del lab",
        "met.rules": [
            ("Niente dati futuri", "Le feature sono point-in-time: il segnale nasce dopo il close, l'entry simulata è al next open. Chi guarda avanti, bara."),
            ("Split purgato + embargo", "Le ultime barre di train/validation/test vengono rimosse quando la label forward supererebbe il confine temporale."),
            ("Test set intoccabile", "Il tuning vive su validation; la calibrazione delle probabilità si fitta solo su validation. Il test si guarda una volta."),
            ("Preregistrazione", "Ogni trial dichiara prima ipotesi, metrica primaria e criteri di successo. Il trial counter e il multiplicity budget impediscono di riprovare finché non esce bene."),
            ("DSR & permutation test", "Deflated Sharpe Ratio contro il numero di tentativi, permutation test contro la fortuna. Sotto ~100 trade nessun risultato distingue edge da rumore."),
            ("Regola degli outlier", "Se il risultato cambia segno togliendo i top 3 trade vincenti, non è promuovibile. Punto."),
            ("Run manifest", "Ogni run ha run_id, config hash SHA-256, git commit e host. Se non è riproducibile, non esiste."),
            ("Verdetti onesti", "I fallimenti restano nel vault come report: baseline large-cap = controllo negativo, small-cap EMA200 = archiviata. Nessun cherry-picking."),
        ],
        "met.not.lbl": "Cosa NON è questo sito",
        "met.not.p": ("Non è un bot, non è un servizio di segnali, non è una prova di profittabilità. I dati sono proxy "
                      "(yfinance daily, non point-in-time, survivorship bias incluso) e ogni numero che vedi è diagnostica "
                      "di ricerca su quel campione. Niente qui autorizza decisioni di capitale reale — ed è esattamente "
                      "il punto: il lab esiste per dimostrare il processo, non per vendere un risultato."),
        "footer.left": "Adaptive Equity Trading Lab — progettato e costruito da Abed Barakat",
        "footer.right": "dati proxy, nessun consiglio d'investimento",
    },
    "en": {
        "nav.home": "Home", "nav.arena": "Arena", "nav.regimes": "Regimes",
        "nav.composer": "Composer", "nav.method": "Method", "nav.regime": "Regime",
        "settings": "Catalog settings",
        "settings.saved": "Saved workbench (max)", "settings.factory": "Generated factory variants",
        "na": "n/a", "offscale": "off scale", "offscale.restart": "off scale (restart the server)",
        "hero.kicker": "Adaptive Equity Trading Lab — governed quantitative research",
        "hero.h1": 'Every market regime has its own <span>best portfolio</span>.<br>Here you find it, see it, compose it.',
        "hero.p": ("This lab does not sell a winning strategy: it builds a process that cannot cheat. "
                   "The Studio tests the whole strategy catalog, asks the regime router which families are allowed "
                   "in each market state, finds the best basket for every regime and composes them into a single "
                   "portfolio that changes skin when the market does."),
        "hero.disc": "Proxy data · diagnostics · no promotion / no live trading",
        "engine.lbl": "How the engine works",
        "engine.nodes": ["Data & snapshots", "Data gates", "Preregistered trials",
                         "DSR & multiplicity budget", "Regime router", "Basket per regime", "Portfolio Composer"],
        "engine.p1": ("Every idea enters as a <b>preregistered trial</b>: hypothesis, primary metric and success criteria "
                      "declared before seeing any result. Statistical gates — Deflated Sharpe Ratio, permutation tests, "
                      "multiplicity budgets — decide what survives. The <b>regime router</b> sets which strategy families "
                      "may play in each market state, and the <b>Composer</b> assembles them into a regime-switching "
                      "portfolio benchmarked against honest baselines."),
        "engine.p2": ("The most important result so far is not a profitable strategy: it is a system that "
                      "<b>repeatedly refuses to promote weak evidence</b>. The full story lives in the Method page."),
        "tiles.catalog": "Strategies in catalog", "tiles.catalog.n": "Saved workbench + factory generated",
        "tiles.families": "Strategy families", "tiles.families.n": "Momentum, mean reversion, events, regime...",
        "tiles.regimes": "Mapped regimes", "tiles.regimes.n": "Market states from the regime router",
        "tiles.positive": "Positive strategies", "tiles.positive.n": "On the local proxy path — not a promise",
        "steps.1n": "01 — TEST", "steps.1t": "Strategy Arena",
        "steps.1d": "The whole catalog side by side: filter by family, sort by net, open each curve and read its bias warnings.",
        "steps.2n": "02 — GOVERN", "steps.2t": "Regimes",
        "steps.2d": "The Strategy × Regime matrix: who is allowed, who plays at half size, who stays out when the market changes state.",
        "steps.3n": "03 — COMPOSE", "steps.3t": "Composer",
        "steps.3d": "The best basket for each regime, composed into a dynamic portfolio benchmarked against honest baselines and permutation tests.",
        "cta.arena": "Open the Strategy Arena", "cta.composer": "Compose the portfolio",
        "arena.title": "Strategy Arena",
        "arena.sub": 'The whole catalog, tested on local streams. Sort, filter, open the curve. "u" = additive proxy units, not percentages.',
        "arena.empty": "No strategies in catalog. Create dry-runs in the Workbench or enable the factory.",
        "arena.f.family": "Family", "arena.f.source": "Source", "arena.f.order": "Sort by",
        "arena.o.netdesc": "Net (desc)", "arena.o.netasc": "Net (asc)", "arena.o.trades": "Trades (desc)", "arena.o.warn": "Warnings (asc)",
        "arena.k.filtered": "Filtered strategies", "arena.k.filtered.n": "In the current set",
        "arena.k.best": "Best", "arena.k.median": "Median", "arena.k.median.n": "Half the catalog does worse than this",
        "arena.open": "Open a strategy", "arena.select": "Strategy",
        "arena.nostream": "No stream available for this strategy.",
        "arena.d.net": "Net", "arena.d.net.n": "End of the local path", "arena.d.trades": "Trades",
        "arena.d.trades.n": "Dry-run sample", "arena.d.family": "Family", "arena.d.warn": "Bias warnings",
        "arena.caption": "Local proxy curve. Below N~100 trades no result can tell edge from luck (see PCTRL power curve).",
        "col.name": "Strategy", "col.family": "Family", "col.source": "Source", "col.trades": "Trades",
        "col.net": "Net", "col.decision": "Decision", "col.warnings": "Warnings",
        "reg.title": "Strategy × Regime",
        "reg.sub": "The router decides who plays in each market state. ALLOW plays, REDUCE plays at half size, OVERLAY governs risk, BLOCK stays out.",
        "reg.warn": "Router matrix not available.",
        "reg.caption": "The matrix comes from the lab's archived evidence: it is defensive governance, not proven alpha.",
        "reg.baskets": "The best basket for each regime",
        "reg.baskets.caption": "Governed search over the components allowed in that regime only. The first run takes a few minutes, then stays cached.",
        "reg.baskets.btn": "Compute per-regime baskets",
        "reg.basket.meta": "components in basket · allowed {a} / blocked {b}",
        "comp.title": "Portfolio Composer",
        "comp.sub": "A portfolio that switches basket when the market switches regime, benchmarked against the static equal-weight baseline. Proxy diagnostics: not promotable.",
        "comp.weights": "Weights inside each basket",
        "comp.btn": "Compose the regime-switching portfolio",
        "comp.info": "Press the button: the Studio optimizes a basket per regime and composes them over time. The first run takes a few minutes.",
        "comp.warn": "Composition not available: streams with real dates are required.",
        "comp.dynamic": "Dynamic", "comp.dynamic.n": "Regime-switching portfolio",
        "comp.static": "Honest static", "comp.static.n": "Equal-weight, real-cost components only (<=100bps), dedup",
        "comp.top5": "Top-5 without routing", "comp.top5.n": "Simple selection, no regime switching",
        "comp.dd": "Dynamic max DD",
        "comp.dd.n": "Honest static vs legacy: the legacy one ({v}) is inflated by cost tiers",
        "comp.perm.ok": "Permutation test ({n} regime-label shifts): p = {p}. Regime TIMING is statistically supported on this sample.",
        "comp.perm.warn": ("Permutation test ({n} regime-label shifts): p = {p}. The value comes from component SELECTION, "
                           "not regime timing (verdict TRIAL-STUDIO-OOS-008, audit 2026-06-11). The old 'static' baseline was inflated by cost tiers."),
        "comp.usage": "Periods per regime",
        "comp.baskets": "The chosen baskets, regime by regime",
        "comp.components": "components", "comp.weight": "weight", "comp.others": "...and {n} more",
        "comp.delta.pos": "On this local path regime switching ADDS {v} over the static baseline. Still a proxy diagnostic: the true data gate comes before any claim.",
        "comp.delta.neg": "On this local path regime switching REMOVES {v} versus the static baseline: regime rules are defensive governance, not proven return enhancement.",
        "comp.caption": "Proxy sample, selection-surviving strategies, additive streams: this number authorizes no real-capital decision.",
        "met.title": "Method & guarantees",
        "met.sub": "The rules every experiment must respect before a number is taken seriously. They are wired into the code, not written on a post-it.",
        "met.story.lbl": "The story, in short",
        "met.story.p1": ("The lab started as a large-cap ML pipeline. When the backtest failed to beat buy-and-hold, "
                         "the failure was documented and the baseline <b>demoted to a negative control</b> instead of being tweaked "
                         'until it "worked". The following small-cap track produced an apparent +169% edge: '
                         "the sizing audit dismantled it, reclassifying it as a <b>leverage and path artifact</b> — archived, not promoted."),
        "met.story.p2": ("Today the lab runs as a <b>risk &amp; regime engine</b>: zero promoted strategies, one portfolio rule "
                         "preregistered and <b>frozen</b> (2026-06-11), an out-of-sample replica scheduled on the first of every month "
                         "with no modification allowed. The value measured so far comes from <b>component selection</b>, "
                         "not regime timing: the permutation test says so, and the Composer page shows it without tricks."),
        "met.rules.lbl": "The eight rules of the lab",
        "met.rules": [
            ("No future data", "Features are point-in-time: the signal is born after the close, the simulated entry is at next open. Looking ahead is cheating."),
            ("Purged split + embargo", "The last bars of train/validation/test are removed whenever the forward label would cross the time boundary."),
            ("Untouchable test set", "Tuning lives on validation; probability calibration is fitted on validation only. The test set is looked at once."),
            ("Preregistration", "Every trial declares hypothesis, primary metric and success criteria upfront. The trial counter and multiplicity budget prevent retrying until it looks good."),
            ("DSR & permutation tests", "Deflated Sharpe Ratio against the number of attempts, permutation tests against luck. Below ~100 trades no result can tell edge from noise."),
            ("Outlier rule", "If the result flips sign when the top 3 winning trades are removed, it is not promotable. Period."),
            ("Run manifest", "Every run has a run_id, SHA-256 config hash, git commit and host. If it is not reproducible, it does not exist."),
            ("Honest verdicts", "Failures stay in the vault as reports: large-cap baseline = negative control, small-cap EMA200 = archived. No cherry-picking."),
        ],
        "met.not.lbl": "What this site is NOT",
        "met.not.p": ("It is not a bot, not a signal service, not a proof of profitability. Data is proxy "
                      "(yfinance daily, not point-in-time, survivorship bias included) and every number you see is research "
                      "diagnostics on that sample. Nothing here authorizes real-capital decisions — and that is exactly "
                      "the point: the lab exists to demonstrate the process, not to sell a result."),
        "footer.left": "Adaptive Equity Trading Lab — designed & built by Abed Barakat",
        "footer.right": "proxy data, not investment advice",
    },
}


def lang() -> str:
    return str(st.session_state.get("studio_lang", "it"))


def tr(key: str) -> str:
    return str(T.get(lang(), T["it"]).get(key, T["it"].get(key, key)))


def trl(key: str) -> list:
    value = T.get(lang(), T["it"]).get(key, T["it"].get(key, []))
    return list(value) if isinstance(value, (list, tuple)) else []


def regime_label(regime: str) -> str:
    return REGIME_LABELS.get(lang(), REGIME_LABELS["it"]).get(regime, regime)


# ---------------------------------------------------------------------------
# theme: carta e inchiostro, stile report di ricerca (abedbarakat.me)
# ---------------------------------------------------------------------------

def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        :root {
          --bg: #f4f2ee;
          --panel: #faf9f6;
          --line: rgba(59,59,59,.16);
          --line-soft: rgba(59,59,59,.09);
          --ink: #3b3b3b;
          --soft: #565550;
          --muted: #6f6f6f;
          --accent: #2f7d62;
          --warn: #9a6a12;
          --bad: #b5462f;
          --plum: #6b4f8a;
          --blue: #3b6ea5;
          --head: 'Archivo', sans-serif;
          --body: 'Inter', sans-serif;
        }
        [data-testid="stHeader"], #MainMenu, footer { display:none !important; }
        section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display:none !important; }
        html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--ink); font-family: var(--body); }
        .block-container { padding-top: 1.4rem; padding-bottom: 4rem; max-width: 1280px; }
        h1,h2,h3,h4 { font-family: var(--head); color: var(--ink); }

        .studio-logo { font-family:var(--head); font-weight:700; font-size:17px; letter-spacing:.01em; text-transform:uppercase; color:var(--ink); }
        .studio-tag { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.18em; margin-top:3px; }

        .stButton > button {
          background: transparent; color: var(--soft);
          border: 1px solid var(--line); border-radius: 2px;
          font-family: var(--body); font-weight:600; font-size:13.5px;
          transition: border-color .15s ease, color .15s ease;
        }
        .stButton > button:hover { color: var(--ink); border-color: var(--ink); }
        .stButton > button[kind="primary"] {
          background: var(--ink); border: 1px solid var(--ink); color: var(--bg);
        }
        .stButton > button[kind="primary"]:hover { background: #262624; color:#fff; }

        .hero { border-top: 3px solid var(--ink); border-bottom: 1px solid var(--line); padding: 42px 4px 38px; margin-bottom: 14px; }
        .hero-kicker { color: var(--muted); font-size: 11.5px; letter-spacing:.22em; text-transform:uppercase; font-weight:600; }
        .hero h1 { font-family: var(--head); text-transform: uppercase; font-size: 44px; line-height:1.05; letter-spacing:-.01em; margin: 16px 0 16px; font-weight:700; }
        .hero h1 span { color: var(--accent); }
        .hero p { color: var(--soft); font-size: 16px; max-width: 760px; line-height: 1.65; margin:0; }
        .hero .disclaimer { margin-top: 18px; display:inline-block; font-size: 11px; color: var(--warn); border:1px solid rgba(154,106,18,.35); padding: 6px 13px; letter-spacing:.08em; text-transform:uppercase; font-weight:600; }

        .tile { background: var(--panel); border: 1px solid var(--line); border-radius:2px; padding: 16px 18px; height: 100%; }
        .tile .k { color: var(--muted); font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .14em; }
        .tile .v { font-family: var(--head); font-size: 28px; font-weight: 700; margin-top: 7px; letter-spacing:-.01em; font-variant-numeric: tabular-nums; color: var(--ink); }
        .tile .v.pos { color: var(--accent); } .tile .v.neg { color: var(--bad); }
        .tile .n { color: var(--muted); font-size: 12px; margin-top: 5px; line-height:1.5; }

        .step-grid { display:grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin: 8px 0 4px; }
        .step { border:1px solid var(--line); border-radius:2px; padding:22px; background: var(--panel); }
        .step .num { color: var(--muted); font-size: 11px; font-weight:600; letter-spacing:.16em; }
        .step .t { font-family:var(--head); font-weight:700; font-size: 17px; margin: 10px 0 7px; text-transform:uppercase; }
        .step .d { color: var(--muted); font-size: 13px; line-height: 1.6; }
        .step .bar { width:34px; height:3px; background: var(--ink); margin-top:10px; }

        .badge { display:inline-block; padding: 3px 10px; border-radius: 2px; font-size: 10.5px; font-weight:700; letter-spacing:.08em; text-transform: uppercase; border: 1px solid; }
        .badge.go { color: var(--accent); border-color: rgba(47,125,98,.45); background: rgba(47,125,98,.07); }
        .badge.cut { color: var(--bad); border-color: rgba(181,70,47,.45); background: rgba(181,70,47,.06); }
        .badge.hold { color: var(--warn); border-color: rgba(154,106,18,.4); background: rgba(154,106,18,.06); }
        .badge.mute { color: var(--muted); border-color: var(--line); background: rgba(59,59,59,.04); }
        .badge.plum { color: var(--plum); border-color: rgba(107,79,138,.4); background: rgba(107,79,138,.06); }
        .badge.blue { color: var(--blue); border-color: rgba(59,110,165,.4); background: rgba(59,110,165,.06); }

        .regime-chip { display:inline-flex; align-items:center; gap:8px; padding: 7px 13px; border:1px solid var(--line); background: var(--panel); font-size: 12.5px; font-weight:600; border-radius:2px; }
        .regime-dot { width:9px; height:9px; border-radius:50%; display:inline-block; }

        .section-title { font-family:var(--head); text-transform:uppercase; font-size: 24px; font-weight: 700; letter-spacing: -.01em; margin: 10px 0 2px; border-top:3px solid var(--ink); padding-top:14px; }
        .section-sub { color: var(--muted); font-size: 13.5px; margin: 4px 0 14px; max-width: 900px; line-height:1.55; }

        .story { border:1px solid var(--line); border-radius:2px; background:var(--panel); padding:26px 28px; margin: 12px 0; }
        .story .lbl { color:var(--muted); font-size:11px; letter-spacing:.2em; text-transform:uppercase; font-weight:600; margin-bottom:12px; }
        .story p { color:var(--soft); font-size:14.5px; line-height:1.7; margin:0 0 10px; max-width: 960px; }
        .story p:last-child { margin-bottom:0; }
        .story b { color: var(--ink); }
        .pipe { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:6px; }
        .pipe .node { border:1px solid var(--line); background:var(--bg); border-radius:2px; padding:7px 13px; font-size:12.5px; font-weight:600; color:var(--soft); }
        .pipe .node.hot { border-color: var(--ink); color: var(--ink); }
        .pipe .arr { color: var(--muted); font-size:13px; }
        .rule-row { display:flex; gap:16px; align-items:flex-start; padding:14px 0; border-top:1px solid var(--line-soft); }
        .rule-row .no { color:var(--muted); font-size:12px; font-weight:600; letter-spacing:.1em; min-width:28px; padding-top:2px; }
        .rule-row .tt { font-weight:700; font-size:14.5px; color:var(--ink); font-family:var(--head); }
        .rule-row .dd { color:var(--muted); font-size:13px; line-height:1.55; margin-top:3px; }

        [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius: 2px; overflow:hidden; }
        [data-testid="stExpander"] details { background: var(--panel); border:1px solid var(--line) !important; border-radius: 2px !important; }
        .stPlotlyChart { background: var(--panel); border:1px solid var(--line); border-radius: 2px; padding: 10px; }
        .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label { color: var(--soft) !important; font-size: 13px !important; }
        .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
        .stTabs [data-baseweb="tab"] { color: var(--muted); }
        .stTabs [aria-selected="true"] { color: var(--ink) !important; }

        .lab-footer { border-top:1px solid var(--line); margin-top:44px; padding:16px 2px 0; display:flex; justify-content:space-between; align-items:center; color:var(--muted); font-size:12px; flex-wrap:wrap; gap:8px; }
        .lab-footer a { color: var(--soft); text-decoration:none; border-bottom:1px solid var(--line); }
        .lab-footer a:hover { color: var(--accent); border-color: var(--accent); }
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
        return tr("na")
    if not math.isfinite(number):
        return tr("na")
    if str(mode) == "compounded":
        if abs(number) > 100:
            return tr("offscale")
        prefix = "+" if signed and number > 0 else ""
        return f"{prefix}{number * 100:.1f}%"
    if abs(number) > 1e9:
        return tr("offscale.restart")
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
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=24, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#565550", size=12),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(gridcolor="rgba(59,59,59,.10)")
    fig.update_yaxes(gridcolor="rgba(59,59,59,.10)")
    return fig


# ---------------------------------------------------------------------------
# cached data layer (colonne interne in inglese, display tradotto)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading strategy catalog…")
def load_catalog(saved_limit: int, factory_variants: int) -> list[dict]:
    saved = load_portfolio_lab_components(limit=saved_limit)
    factory = build_strategy_factory_components(max_variants=factory_variants) if factory_variants else []
    return [*saved, *factory]


@st.cache_data(show_spinner="Loading router & regime map…")
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


@st.cache_data(show_spinner="Optimizing per-regime baskets… (first run takes a few minutes)")
def run_studio_cached(saved_limit: int, factory_variants: int, policy: str) -> dict:
    catalog = load_catalog(saved_limit, factory_variants)
    context = load_market_context()
    return run_regime_studio(catalog, context["router_matrix"], context["regime_map"], policy=policy)


@st.cache_data(show_spinner="Computing honest baselines & permutation test… (~1 min first run)")
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
                "name": str(component.get("strategy_name")),
                "family": component_strategy_family(component),
                "source": str(component.get("source", "saved_workbench")).replace("_", " "),
                "trades": int(component.get("trade_count") or 0),
                "net": float(curve.iloc[-1]) if len(curve) else 0.0,
                "mode": mode,
                "decision": str(component.get("decision", "")).replace("_", " "),
                "warnings": len(component.get("bias_warnings", []) or []),
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
        st.session_state["studio_section"] = "home"
    if "studio_lang" not in st.session_state:
        st.session_state["studio_lang"] = "it"
    cols = st.columns([2.1, 0.75, 0.75, 0.85, 1.0, 0.85, 0.42, 0.42, 1.9])
    with cols[0]:
        st.markdown(
            '<div class="studio-logo">Portfolio <b>Studio</b></div>'
            '<div class="studio-tag">Adaptive Equity Trading Lab</div>',
            unsafe_allow_html=True,
        )
    for column, section in zip(cols[1:6], SECTIONS):
        with column:
            kind = "primary" if st.session_state["studio_section"] == section else "secondary"
            if st.button(tr(f"nav.{section}"), key=f"nav_{section}", type=kind, width="stretch"):
                st.session_state["studio_section"] = section
                st.rerun()
    for column, code in zip(cols[6:8], ["it", "en"]):
        with column:
            kind = "primary" if lang() == code else "secondary"
            if st.button(code.upper(), key=f"lang_{code}", type=kind, width="stretch"):
                st.session_state["studio_lang"] = code
                st.rerun()
    with cols[8]:
        current = load_market_context()["current_regime"]
        label = str(current.get("regime_label", "n/d"))
        color = REGIME_COLORS.get(label, "#8a877f")
        st.markdown(
            f'<div class="regime-chip" style="float:right"><span class="regime-dot" style="background:{color}"></span>'
            f'{tr("nav.regime")}: {regime_label(label)}</div>',
            unsafe_allow_html=True,
        )
    return str(st.session_state["studio_section"])


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def page_home(saved_limit: int, factory_variants: int) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">{tr("hero.kicker")}</div>
          <h1>{tr("hero.h1")}</h1>
          <p>{tr("hero.p")}</p>
          <div class="disclaimer">{tr("hero.disc")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nodes = trl("engine.nodes")
    pipe = '<span class="arr">&rarr;</span>'.join(
        f'<span class="node{" hot" if index >= 4 else ""}">{node}</span>' for index, node in enumerate(nodes)
    )
    st.markdown(
        f"""
        <div class="story">
          <div class="lbl">{tr("engine.lbl")}</div>
          <div class="pipe">{pipe}</div>
          <p style="margin-top:14px">{tr("engine.p1")}</p>
          <p>{tr("engine.p2")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    table = strategy_table(saved_limit, factory_variants)
    context = load_market_context()
    regimes = context["router_matrix"]["regime_label"].nunique() if not context["router_matrix"].empty else 0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tile(tr("tiles.catalog"), f"{len(table)}", tr("tiles.catalog.n"))
    with c2:
        tile(tr("tiles.families"), f"{table['family'].nunique() if not table.empty else 0}", tr("tiles.families.n"))
    with c3:
        tile(tr("tiles.regimes"), f"{regimes}", tr("tiles.regimes.n"))
    with c4:
        positive = int((table["net"] > 0).sum()) if not table.empty else 0
        tile(tr("tiles.positive"), f"{positive}/{len(table)}", tr("tiles.positive.n"), tone="pos" if positive else "")
    st.markdown(
        f"""
        <div class="step-grid">
          <div class="step"><div class="num">{tr("steps.1n")}</div><div class="t">{tr("steps.1t")}</div>
            <div class="d">{tr("steps.1d")}</div><div class="bar"></div></div>
          <div class="step"><div class="num">{tr("steps.2n")}</div><div class="t">{tr("steps.2t")}</div>
            <div class="d">{tr("steps.2d")}</div><div class="bar"></div></div>
          <div class="step"><div class="num">{tr("steps.3n")}</div><div class="t">{tr("steps.3t")}</div>
            <div class="d">{tr("steps.3d")}</div><div class="bar"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cta1, cta2, _ = st.columns([1.2, 1.2, 3])
    with cta1:
        if st.button(tr("cta.arena"), type="primary", width="stretch"):
            st.session_state["studio_section"] = "arena"
            st.rerun()
    with cta2:
        if st.button(tr("cta.composer"), width="stretch"):
            st.session_state["studio_section"] = "composer"
            st.rerun()


def display_columns() -> dict:
    return {
        "name": tr("col.name"), "family": tr("col.family"), "source": tr("col.source"),
        "trades": tr("col.trades"), "net": tr("col.net"), "decision": tr("col.decision"),
        "warnings": tr("col.warnings"),
    }


def page_arena(saved_limit: int, factory_variants: int) -> None:
    st.markdown(f'<div class="section-title">{tr("arena.title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{tr("arena.sub")}</div>', unsafe_allow_html=True)
    table = strategy_table(saved_limit, factory_variants)
    if table.empty:
        st.warning(tr("arena.empty"))
        return
    f1, f2, f3 = st.columns([1.4, 1.4, 1.2])
    with f1:
        families = st.multiselect(tr("arena.f.family"), sorted(table["family"].unique()), default=[])
    with f2:
        sources = st.multiselect(tr("arena.f.source"), sorted(table["source"].unique()), default=[])
    with f3:
        order_keys = ["arena.o.netdesc", "arena.o.netasc", "arena.o.trades", "arena.o.warn"]
        order = st.selectbox(tr("arena.f.order"), order_keys, format_func=tr)
    view = table.copy()
    if families:
        view = view[view["family"].isin(families)]
    if sources:
        view = view[view["source"].isin(sources)]
    by, asc = {
        "arena.o.netdesc": ("net", False), "arena.o.netasc": ("net", True),
        "arena.o.trades": ("trades", False), "arena.o.warn": ("warnings", True),
    }[order]
    view = view.sort_values(by, ascending=asc).reset_index(drop=True)

    k1, k2, k3 = st.columns(3)
    mode_overall = "compounded" if (view["mode"] == "compounded").all() else "additive"
    with k1:
        tile(tr("arena.k.filtered"), f"{len(view)}", tr("arena.k.filtered.n"))
    with k2:
        best_value = view["net"].max() if not view.empty else 0.0
        tile(tr("arena.k.best"), fmt_net(best_value, mode_overall), str(view.iloc[0]["name"])[:42] if not view.empty else "-", tone=tone_of(best_value))
    with k3:
        med = view["net"].median() if not view.empty else 0.0
        tile(tr("arena.k.median"), fmt_net(med, mode_overall), tr("arena.k.median.n"), tone=tone_of(med))

    show = view.copy()
    show["net"] = [fmt_net(v, m) for v, m in zip(view["net"], view["mode"])]
    show = show.drop(columns=["id", "mode"]).rename(columns=display_columns())
    st.dataframe(show, width="stretch", hide_index=True, height=420)

    st.markdown(f"##### {tr('arena.open')}")
    labels = {row["id"]: f'{row["name"]}  ·  {row["family"]}  ·  {fmt_net(row["net"], row["mode"])}' for _, row in view.iterrows()}
    if not labels:
        return
    chosen = st.selectbox(tr("arena.select"), list(labels), format_func=lambda key: labels[key])
    curve = strategy_curve(saved_limit, factory_variants, chosen)
    if curve.empty:
        st.info(tr("arena.nostream"))
        return
    row = view[view["id"] == chosen].iloc[0]
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        tile(tr("arena.d.net"), fmt_net(row["net"], row["mode"]), tr("arena.d.net.n"), tone=tone_of(row["net"]))
    with d2:
        tile(tr("arena.d.trades"), f'{row["trades"]}', tr("arena.d.trades.n"))
    with d3:
        tile(tr("arena.d.family"), FAMILY_GLYPH.get(row["family"], ""), row["family"])
    with d4:
        tile(tr("arena.d.warn"), f'{row["warnings"]}', row["decision"] or "diagnostic")
    fig = go.Figure(go.Scatter(x=curve["period"], y=curve["value"], mode="lines", line=dict(color="#2f7d62", width=2.4), fill="tozeroy", fillcolor="rgba(47,125,98,.08)", name="curve"))
    st.plotly_chart(chart_layout(fig, height=320), width="stretch")
    st.caption(tr("arena.caption"))


def page_regimes(saved_limit: int, factory_variants: int) -> None:
    st.markdown(f'<div class="section-title">{tr("reg.title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{tr("reg.sub")}</div>', unsafe_allow_html=True)
    context = load_market_context()
    matrix = context["router_matrix"]
    if matrix.empty:
        st.warning(tr("reg.warn"))
        return
    regimes = sorted(matrix["regime_label"].astype(str).unique())
    families = sorted(matrix["strategy_family"].astype(str).unique())
    posture_of = {(str(r["regime_label"]), str(r["strategy_family"])): str(r["posture"]) for _, r in matrix.iterrows()}
    header = "".join(
        f'<th style="padding:8px 10px;text-align:left"><span class="regime-chip"><span class="regime-dot" style="background:{REGIME_COLORS.get(regime, "#8a877f")}"></span>{regime_label(regime)}</span></th>'
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
    st.caption(tr("reg.caption"))

    st.markdown(f"##### {tr('reg.baskets')}")
    st.caption(tr("reg.baskets.caption"))
    if st.button(tr("reg.baskets.btn"), type="primary"):
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
            meta = tr("reg.basket.meta").format(a=basket.get("allowed_count", 0), b=basket.get("blocked_count", 0))
            with columns[index % 3]:
                color = REGIME_COLORS.get(regime, "#8a877f")
                st.markdown(
                    f"""
                    <div class="tile" style="border-top:3px solid {color}; margin-bottom:12px">
                      <div class="k">{regime_label(regime)}</div>
                      <div class="v {tone_of(net)}">{fmt_net(net, mode)}</div>
                      <div class="n">{len(basket.get("basket_component_ids", []))} {meta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def page_composer(saved_limit: int, factory_variants: int) -> None:
    st.markdown(f'<div class="section-title">{tr("comp.title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{tr("comp.sub")}</div>', unsafe_allow_html=True)
    policy = st.radio(tr("comp.weights"), ["equal_weight", "inverse_volatility", "sleeve_allocation"], horizontal=True)
    if st.button(tr("comp.btn"), type="primary"):
        st.session_state["studio_composed"] = policy
    chosen_policy = st.session_state.get("studio_composed")
    if not chosen_policy:
        st.info(tr("comp.info"))
        return
    studio = run_studio_cached(saved_limit, factory_variants, str(chosen_policy))
    composition = studio.get("composition", {})
    summary = composition.get("summary", {}) or {}
    if not summary:
        st.warning(tr("comp.warn"))
        return
    mode = str(summary.get("aggregation_mode", "additive"))
    honest = honest_baselines_cached(saved_limit, factory_variants)
    hr = honest.get("results", {})
    perm = honest.get("permutation", {})
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tile(tr("comp.dynamic"), fmt_net(summary.get("dynamic_total"), mode), tr("comp.dynamic.n"), tone=tone_of(summary.get("dynamic_total")))
    with c2:
        tile(tr("comp.static"), fmt_net(hr.get("static_cost_matched"), "compounded"), tr("comp.static.n"), tone=tone_of(hr.get("static_cost_matched")))
    with c3:
        tile(tr("comp.top5"), fmt_net(hr.get("unconditional_top5"), "compounded"), tr("comp.top5.n"), tone=tone_of(hr.get("unconditional_top5")))
    with c4:
        tile(
            tr("comp.dd"),
            fmt_net(summary.get("dynamic_max_drawdown"), mode, signed=False),
            tr("comp.dd.n").format(v=fmt_net(hr.get("static_all_legacy"), "compounded")),
            tone=tone_of(summary.get("dynamic_max_drawdown")),
        )
    p_value = perm.get("p_value")
    if p_value is not None:
        if float(p_value) <= 0.05:
            st.success(tr("comp.perm.ok").format(n=perm.get("n", 0), p=p_value))
        else:
            st.warning(tr("comp.perm.warn").format(n=perm.get("n", 0), p=p_value))

    curves = composition.get("curves")
    if isinstance(curves, pd.DataFrame) and not curves.empty:
        fig = go.Figure()
        segment_start = 0
        rows = curves.reset_index(drop=True)
        for i in range(1, len(rows) + 1):
            if i == len(rows) or rows.loc[i, "regime"] != rows.loc[segment_start, "regime"]:
                regime = rows.loc[segment_start, "regime"]
                fig.add_vrect(
                    x0=rows.loc[segment_start, "period"], x1=rows.loc[min(i, len(rows) - 1), "period"],
                    fillcolor=REGIME_COLORS.get(str(regime), "#8a877f"), opacity=0.07, line_width=0,
                )
                segment_start = i
        fig.add_trace(go.Scatter(x=rows["period"], y=rows["static"], name="Static", mode="lines", line=dict(color="#8a877f", width=1.8, dash="dot")))
        fig.add_trace(go.Scatter(x=rows["period"], y=rows["dynamic"], name="Dynamic", mode="lines", line=dict(color="#2f7d62", width=2.6)))
        st.plotly_chart(chart_layout(fig, height=430), width="stretch")
        legend = "  ".join(
            f'<span class="regime-chip" style="margin-right:6px"><span class="regime-dot" style="background:{REGIME_COLORS.get(r, "#8a877f")}"></span>{regime_label(r)}</span>'
            for r in rows["regime"].unique()
        )
        st.markdown(legend, unsafe_allow_html=True)

    usage = composition.get("regime_usage")
    baskets = studio.get("baskets_by_regime", {})
    u1, u2 = st.columns([1.1, 1.6])
    with u1:
        if isinstance(usage, pd.DataFrame) and not usage.empty:
            fig = go.Figure(go.Bar(
                x=usage["periods"], y=[regime_label(r) for r in usage["regime"]],
                orientation="h", marker=dict(color=[REGIME_COLORS.get(str(r), "#8a877f") for r in usage["regime"]]),
            ))
            fig.update_layout(title=tr("comp.usage"))
            st.plotly_chart(chart_layout(fig, height=300), width="stretch")
    with u2:
        st.markdown(f"**{tr('comp.baskets')}**")
        table = strategy_table(saved_limit, factory_variants)
        name_of = dict(zip(table["id"], table["name"])) if not table.empty else {}
        for regime, basket in baskets.items():
            ids = basket.get("basket_component_ids", [])
            with st.expander(f"{regime_label(regime)} - {len(ids)} {tr('comp.components')}"):
                for component_id in ids[:12]:
                    weight = basket.get("weights", {}).get(component_id, 0.0)
                    st.markdown(f'- `{component_id[:18]}` {name_of.get(component_id, "")} — {tr("comp.weight")} {weight:.0%}')
                if len(ids) > 12:
                    st.caption(tr("comp.others").format(n=len(ids) - 12))

    delta = float(summary.get("dynamic_vs_static_delta", 0.0) or 0.0)
    if delta > 0:
        st.success(tr("comp.delta.pos").format(v=fmt_net(delta, mode)))
    else:
        st.warning(tr("comp.delta.neg").format(v=fmt_net(abs(delta), mode)))
    st.caption(tr("comp.caption"))


def page_method() -> None:
    st.markdown(f'<div class="section-title">{tr("met.title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{tr("met.sub")}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="story">
          <div class="lbl">{tr("met.story.lbl")}</div>
          <p>{tr("met.story.p1")}</p>
          <p>{tr("met.story.p2")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rows = "".join(
        f'<div class="rule-row"><div class="no">{index:02d}</div><div><div class="tt">{title}</div><div class="dd">{text}</div></div></div>'
        for index, (title, text) in enumerate(trl("met.rules"), start=1)
    )
    st.markdown(f'<div class="story"><div class="lbl">{tr("met.rules.lbl")}</div>{rows}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="story">
          <div class="lbl">{tr("met.not.lbl")}</div>
          <p>{tr("met.not.p")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        f"""
        <div class="lab-footer">
          <span>{tr("footer.left")}</span>
          <span><a href="https://abedbarakat.me" target="_blank" rel="noopener">abedbarakat.me</a> ·
          <a href="https://github.com/PerfectPoH/adaptive-equity-trading-lab" target="_blank" rel="noopener">GitHub</a> ·
          {tr("footer.right")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    inject_theme()
    section = navigation()
    with st.expander(tr("settings"), expanded=False):
        s1, s2 = st.columns(2)
        with s1:
            saved_limit = st.slider(tr("settings.saved"), 10, 60, 60, 10)
        with s2:
            factory_variants = st.slider(tr("settings.factory"), 0, 96, 48, 12)
    if section == "home":
        page_home(saved_limit, factory_variants)
    elif section == "arena":
        page_arena(saved_limit, factory_variants)
    elif section == "regimes":
        page_regimes(saved_limit, factory_variants)
    elif section == "method":
        page_method()
    else:
        page_composer(saved_limit, factory_variants)
    footer()


if __name__ == "__main__":
    main()
