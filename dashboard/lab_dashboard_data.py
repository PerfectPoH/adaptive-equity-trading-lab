from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


EXECUTION_OUTPUTS_DIR = Path("experiments/provider_aware_research/execution_outputs")
FINAL_STATUS_DIR = EXECUTION_OUTPUTS_DIR / "LAB-FINAL-STATUS-PACK-RUN-001"
FIVE_POINT_DIR = EXECUTION_OUTPUTS_DIR / "TRANSITION-FIVE-POINT-BATCH-RUN-001"
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")


@dataclass(frozen=True)
class StrategyProfile:
    key: str
    name: str
    family: str
    thesis: str
    mechanism: str
    demonstration: list[str]
    decision_pattern: str


STRATEGY_PROFILES: list[StrategyProfile] = [
    StrategyProfile(
        key="xmom",
        name="XMOM / Active-Only Momentum",
        family="Price momentum",
        thesis="Buy the strongest recent small-cap runner and hold the move long-only.",
        mechanism="Ranks symbols by trailing return, enters the top candidate, then tests whether gross momentum survives 500 bps round-trip cost and outlier removal.",
        demonstration=["Archived prices", "63d momentum rank", "Top-1 long", "21d hold", "Cost + robustness gate", "No promotion"],
        decision_pattern="MOMENTUM",
    ),
    StrategyProfile(
        key="gaprev",
        name="GapRev RTH Reversion",
        family="Intraday mean reversion",
        thesis="Buy extreme regular-hours gap-down events after evidence of reclaim/reversion.",
        mechanism="Rejects daily gap illusions, remaps events to RTH-native timestamps, then checks whether the intraday gross move survives realistic taker costs.",
        demonstration=["Daily gap candidate", "RTH timestamp repair", "Opening dislocation", "Reclaim probe", "500 bps cost gate", "Archive"],
        decision_pattern="GAPREV",
    ),
    StrategyProfile(
        key="sec8k",
        name="SEC 8-K Regime / Tape Oracle",
        family="Event-driven volatility",
        thesis="Use Item 2.02 filings as a volatility regime and infer direction from the opening tape.",
        mechanism="Maps SEC event timing, confirms volume/absolute-return lift, then tests whether the first RTH tape direction predicts the rest of session.",
        demonstration=["SEC 8-K Item 2.02", "Event timestamp", "RTH reaction window", "Tape direction", "Cost/sample gate", "Volatility only"],
        decision_pattern="SEC8K",
    ),
    StrategyProfile(
        key="pead",
        name="PEAD / Earnings Surprise",
        family="Academic anomaly",
        thesis="Trade post-earnings drift in the direction of point-in-time earnings surprise.",
        mechanism="Requires actual EPS, consensus EPS, report timing, and revision metadata. Free sources were blocked when PIT quality was missing.",
        demonstration=["Earnings date", "Consensus EPS", "Actual EPS", "SUE direction", "Drift window", "Blocked by PIT data"],
        decision_pattern="PEAD",
    ),
    StrategyProfile(
        key="lowvol",
        name="LowVol / Tradability Filter",
        family="Liquidity and tradability",
        thesis="Prefer more tradable low-volatility small caps to reduce execution damage.",
        mechanism="Filters candidates by volatility/tradability and measures whether the selected panel has positive gross and net return after cost realism.",
        demonstration=["Small-cap panel", "Low-vol filter", "Tradability screen", "Long-only panel", "Median/cost gate", "Archive"],
        decision_pattern="LOWVOL",
    ),
    StrategyProfile(
        key="form4",
        name="Form 4 Cluster Buying",
        family="SEC insider events",
        thesis="Follow clustered open-market insider buys when multiple insiders commit capital in a tight window.",
        mechanism="Queries bounded SEC filings, parses Form 4 transactions, requires clusters and minimum trade count, then blocks when the mini-universe is data-starved.",
        demonstration=["SEC Form 4", "Open-market buy code", "Cluster window", "Liquidity filter", "90-180d hold", "Data-starved archive"],
        decision_pattern="FORM4",
    ),
    StrategyProfile(
        key="dollarbar",
        name="Dollar Bars / Micro-Reversion",
        family="Microstructure data layer",
        thesis="Normalize sampling by traded dollars, then test whether cleaner bars reveal short-horizon reversion.",
        mechanism="Transforms time bars into dollar bars, validates distribution stability, and separately rejects directional micro-reversion when net edge is negative.",
        demonstration=["Intraday bars", "Dollar bucket", "Variance stabilization", "Micro-reversion probe", "Cost gate", "No strategy"],
        decision_pattern="DOLLARBAR",
    ),
    StrategyProfile(
        key="regime",
        name="Regime Map / Risk Engine",
        family="Risk and governance",
        thesis="Stop looking for universal alpha; classify market regimes and restrict which research tracks are allowed.",
        mechanism="Maps volatility/trend/drawdown states, replays archived failures through risk overlays, and freezes small-cap free-data alpha hunting.",
        demonstration=["Local artifacts", "Regime labels", "Risk overlay", "Operating rules", "Final ledger", "Risk engine only"],
        decision_pattern="REGIME",
    ),
]


WORKBENCH_TEMPLATES: dict[str, dict[str, Any]] = {
    "Momentum": {
        "signal": "Rank symbols by trailing return and test top-N long-only continuation.",
        "entry_rule": "Enter the strongest candidate after the ranking window closes.",
        "exit_rule": "Exit after the declared holding period or when the robustness gate fails.",
        "failure_mode": "Outlier dependency and survivorship bias.",
        "required_data": ["daily OHLCV", "survivorship-aware universe", "corporate action adjustment"],
        "default_gate": "outlier_dependency_gate",
        "chart_hint": "The chart must show the ranking window, the entry candle, and the exit candle.",
    },
    "Mean Reversion": {
        "signal": "Find extreme dislocations and test bounded reversion after a confirmation trigger.",
        "entry_rule": "Enter only after a reclaim/confirmation event, not on the falling move itself.",
        "exit_rule": "Exit at the predeclared intraday or multi-day reversion horizon.",
        "failure_mode": "Daily gap illusion, adverse continuation, and cost destruction.",
        "required_data": ["RTH timestamped bars", "spread/slippage proxy", "event purge rules"],
        "default_gate": "cost_realism_gate",
        "chart_hint": "The chart must mark the dislocation, reclaim trigger, entry, and cost gate.",
    },
    "Catalyst": {
        "signal": "Map an external event to a reaction window and require a separate direction source.",
        "entry_rule": "Enter only after event timing and direction source are both known point-in-time.",
        "exit_rule": "Exit inside the declared reaction window; do not hold unmanaged binary risk.",
        "failure_mode": "Volatility without direction and look-ahead contamination.",
        "required_data": ["event timestamp", "reaction session mapping", "point-in-time direction source"],
        "default_gate": "lookahead_bias_gate",
        "chart_hint": "The chart must mark event timestamp, reaction window, and direction source.",
    },
    "PEAD": {
        "signal": "Trade post-earnings drift in the direction of standardized unexpected earnings.",
        "entry_rule": "Enter after the earnings event only when PIT actual-vs-consensus surprise is valid.",
        "exit_rule": "Exit after the drift window defined in the preregistration.",
        "failure_mode": "Missing PIT consensus metadata.",
        "required_data": ["earnings timestamp", "actual EPS", "consensus EPS", "revision metadata"],
        "default_gate": "earnings_pit_quality_gate",
        "chart_hint": "The chart must separate the announcement reaction from the later drift window.",
    },
    "Form 4 Cluster Buying": {
        "signal": "Follow clustered open-market insider purchases after SEC Form 4 validation.",
        "entry_rule": "Enter only after multiple qualified open-market buys appear in the cluster window.",
        "exit_rule": "Exit after a 90-180 day evidence window or when liquidity gates fail.",
        "failure_mode": "Data starvation and low liquidity.",
        "required_data": ["SEC Form 4", "transaction code P", "insider role", "liquidity panel"],
        "default_gate": "event_count_gate",
        "chart_hint": "The chart must mark each insider filing date and the cluster confirmation date.",
    },
    "LowVol Tradability": {
        "signal": "Select tradable, lower-volatility candidates and test whether friction drops enough.",
        "entry_rule": "Enter the filtered basket only when volatility and dollar-volume filters pass.",
        "exit_rule": "Exit on the declared rebalance date.",
        "failure_mode": "Negative gross edge despite better tradability.",
        "required_data": ["daily OHLCV", "dollar volume", "spread proxy", "volatility features"],
        "default_gate": "median_return_gate",
        "chart_hint": "The chart must show why the candidate looked tradable and where the gate rejected it.",
    },
    "Dollar-Bar Microstructure": {
        "signal": "Transform time bars into dollar bars and test whether cleaner sampling reveals edge.",
        "entry_rule": "Enter only after the dollar bucket and micro-reversion trigger both complete.",
        "exit_rule": "Exit at the short-horizon microstructure window.",
        "failure_mode": "Cleaner sampling without directional edge.",
        "required_data": ["intraday bars", "dollar volume", "bucket threshold", "cost model"],
        "default_gate": "sampling_stability_gate",
        "chart_hint": "The chart must explain the conversion from clock time to traded-dollar time.",
    },
    "Regime Filter": {
        "signal": "Classify market state first, then allow or block strategy families by context.",
        "entry_rule": "This is a risk overlay: it permits, blocks, or sizes another strategy.",
        "exit_rule": "Deactivate when the regime label changes or confidence falls below threshold.",
        "failure_mode": "Using a risk map as if it were a standalone alpha signal.",
        "required_data": ["daily OHLCV", "volatility features", "drawdown features"],
        "default_gate": "regime_scope_gate",
        "chart_hint": "The chart must show regime segments and which strategy families are allowed.",
    },
    "PDUFA Run-Up": {
        "signal": "Buy speculative biotech anticipation before a known FDA decision date, then exit before the binary event.",
        "entry_rule": "Enter only inside a preregistered pre-event window with liquidity and catalyst validation.",
        "exit_rule": "Exit before the FDA decision; no overnight binary hold through the event.",
        "failure_mode": "Calendar quality, survivorship bias, and biotech gap risk.",
        "required_data": ["FDA/PDUFA calendar", "biotech universe", "daily OHLCV", "liquidity screen"],
        "default_gate": "binary_event_exit_gate",
        "chart_hint": "The chart must mark entry window, final exit date, and forbidden binary event zone.",
    },
    "13D Activist Follow-On": {
        "signal": "Follow activist 13D filings when Item 4 describes a concrete value-unlocking campaign.",
        "entry_rule": "Enter after Schedule 13D validation and Item 4 classification.",
        "exit_rule": "Exit on the preregistered campaign horizon or when the thesis loses filing support.",
        "failure_mode": "Narrative-only activism and stale filing interpretation.",
        "required_data": ["Schedule 13D", "Item 4 text", "daily OHLCV", "liquidity screen"],
        "default_gate": "filing_intent_gate",
        "chart_hint": "The chart must mark the 13D filing, media reaction, and follow-on horizon.",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_dashboard_payload(root: Path = Path(".")) -> dict[str, Any]:
    final_dir = root / FINAL_STATUS_DIR
    five_dir = root / FIVE_POINT_DIR
    ledger = load_csv(final_dir / "research_phase_closure_ledger.csv")
    phase_summary = load_json(final_dir / "research_phase_summary.json")
    operating_rules = load_json(final_dir / "risk_regime_operating_rules.json")
    final_decision = load_json(final_dir / "final_decision.json")
    regime_map = load_csv(five_dir / "etf_largecap_regime_map.csv")
    allocation = load_csv(five_dir / "portfolio_allocation_smoke.csv")
    smallcap_microstructure = load_csv(five_dir / "smallcap_microstructure_diagnostic.csv")
    data_matrix = load_csv(five_dir / "data_upgrade_decision_matrix.csv")
    return {
        "ledger": ledger,
        "phase_summary": phase_summary,
        "operating_rules": operating_rules,
        "final_decision": final_decision,
        "regime_map": regime_map,
        "allocation": allocation,
        "smallcap_microstructure": smallcap_microstructure,
        "data_matrix": data_matrix,
    }


def strategy_rows(ledger: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for profile in STRATEGY_PROFILES:
        matched = _match_strategy_rows(ledger, profile)
        decisions = matched["decision"].dropna().astype(str).tolist() if not matched.empty else []
        promoted = bool(matched["promotion_allowed"].astype(str).str.lower().eq("true").any()) if "promotion_allowed" in matched else False
        rows.append(
            {
                "key": profile.key,
                "name": profile.name,
                "family": profile.family,
                "runs": int(len(matched)),
                "status": classify_strategy_status(decisions, promoted),
                "thesis": profile.thesis,
                "mechanism": profile.mechanism,
                "primary_decision": decisions[-1] if decisions else "NOT_RUN_IN_LEDGER",
            }
        )
    return pd.DataFrame(rows)


def strategy_detail(profile_key: str, ledger: pd.DataFrame) -> dict[str, Any]:
    profile = next(item for item in STRATEGY_PROFILES if item.key == profile_key)
    matched = _match_strategy_rows(ledger, profile)
    return {
        "profile": profile,
        "runs": matched,
        "status": strategy_rows(ledger).set_index("key").loc[profile_key, "status"],
        "flow_nodes": profile.demonstration,
        "flow_edges": list(zip(profile.demonstration[:-1], profile.demonstration[1:])),
    }


def classify_strategy_status(decisions: list[str], promoted: bool) -> str:
    joined = " ".join(decisions).upper()
    if promoted:
        return "PROMOTED"
    if "BLOCK" in joined or "INSUFFICIENT" in joined:
        return "BLOCKED"
    if "ARCHIVE" in joined or "NO_PROMOTION" in joined or "NO_STRATEGY" in joined:
        return "ARCHIVED"
    if decisions:
        return "DIAGNOSTIC"
    return "NOT RUN"


def governance_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    ledger = payload["ledger"]
    phase = payload["phase_summary"]
    final_decision = payload["final_decision"]
    if ledger.empty:
        return {
            "decision_count": 0,
            "promoted_strategy_count": 0,
            "provider_query_rows": 0,
            "backtest_rows": 0,
            "final_policy": "UNKNOWN",
            "completed_points": 0,
        }
    return {
        "decision_count": int(phase.get("decision_count", len(ledger))),
        "promoted_strategy_count": int(phase.get("promoted_strategy_count", 0)),
        "provider_query_rows": int(phase.get("provider_query_rows", 0)),
        "backtest_rows": int(phase.get("backtest_rows", 0)),
        "final_policy": str(phase.get("final_policy", "UNKNOWN")),
        "completed_points": int(final_decision.get("completed_points", 0)),
    }


def project_capability_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"area": "Governance", "capability": "Pre-run gates, blocked actions, explicit final decisions", "state": "active"},
            {"area": "Validation", "capability": "CPCV, DSR, Neff, outlier/top-k dependency checks", "state": "active"},
            {"area": "Data Quality", "capability": "Provider entitlement checks, PIT/revision metadata blocking", "state": "active"},
            {"area": "Cost Realism", "capability": "500 bps taker model and median/cost gates", "state": "active"},
            {"area": "Microstructure", "capability": "RTH remapping, dollar bars, SEC event timing, liquidity diagnostics", "state": "active"},
            {"area": "Execution Safety", "capability": "No paper/live trading, no short selling, no promotion without gate", "state": "locked"},
            {"area": "Future UX", "capability": "User strategy builder and result explorer", "state": "planned"},
        ]
    )


def project_lifecycle_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "phase": "1. Infrastructure hardening",
                "idea_source": "Initial trading lab architecture",
                "what_happened": "The project first built the research skeleton: reproducible runs, local artifacts, provider-aware data loading, final decisions, and testable gates.",
                "lesson": "Before looking for alpha, the lab needed a way to make every result auditable and repeatable.",
            },
            {
                "phase": "2. Momentum falsification",
                "idea_source": "XMOM and active-only momentum",
                "what_happened": "The first promising curves depended on a tiny number of extreme winners. Removing the top trades flipped the result.",
                "lesson": "A strategy that survives only because of a few outliers is not a durable edge; it is lottery exposure.",
            },
            {
                "phase": "3. Catalyst and gap probes",
                "idea_source": "Earnings, SEC 8-K, GapRev, RTH remapping",
                "what_happened": "The lab found real volatility regimes, especially around SEC 8-K events, but long-only direction and daily-gap assumptions failed under timestamp and cost realism.",
                "lesson": "Market shocks are real, but volatility is not direction. RTH-native timing matters more than appealing daily candles.",
            },
            {
                "phase": "4. Data-quality wall",
                "idea_source": "PEAD, Alpha Vantage, Intrinio, SEC EDGAR",
                "what_happened": "PEAD remained theoretically attractive, but free data could not provide point-in-time consensus metadata with enough audit quality.",
                "lesson": "A correct hypothesis must still be blocked when the data cannot prove what was knowable at the time.",
            },
            {
                "phase": "5. Microstructure and SEC event expansion",
                "idea_source": "Dollar bars, Form 4, insider clusters, active-only Polygon universe",
                "what_happened": "Dollar bars improved data stability, but directional probes still failed. Form 4 cluster buying was data-starved in the mini-universe. Active-only exploration was marked non-promotable.",
                "lesson": "Cleaner data representation helps the lab see better, but it does not manufacture alpha.",
            },
            {
                "phase": "6. Strategic closure",
                "idea_source": "Regime map and risk-engine transition",
                "what_happened": "After repeated honest archives, the lab stopped trying to promote small-cap/free-data directional alpha and reframed itself as a risk-regime engine and strategy validation platform.",
                "lesson": "The project did not fail to find a story; it succeeded at refusing weak stories.",
            },
        ]
    )


def build_workbench_manifest(
    *,
    name: str,
    template: str,
    universe: str,
    holding_period_days: int,
    cost_bps: int,
    allow_provider_query: bool,
) -> dict[str, Any]:
    selected = WORKBENCH_TEMPLATES.get(template, WORKBENCH_TEMPLATES["Momentum"])
    return {
        "strategy_name": name.strip() or "UNTITLED_STRATEGY",
        "template": template,
        "universe": universe,
        "holding_period_days": int(holding_period_days),
        "cost_bps": int(cost_bps),
        "provider_query_allowed": bool(allow_provider_query),
        "promotion_allowed": False,
        "signal_contract": selected["signal"],
        "entry_rule": selected["entry_rule"],
        "exit_rule": selected["exit_rule"],
        "known_failure_mode": selected["failure_mode"],
        "required_data": selected["required_data"],
        "first_gate": selected["default_gate"],
        "chart_requirement": selected["chart_hint"],
        "next_step": "Generate a pre-run gate before any backtest or provider query.",
    }


def build_workbench_flow_nodes(manifest: dict[str, Any]) -> list[str]:
    return [
        f"Template: {manifest['template']}",
        "Data contract",
        "Entry rule",
        "Exit rule",
        f"Gate: {manifest['first_gate']}",
        "Pre-run manifest",
    ]


def build_workbench_chart_story(manifest: dict[str, Any], *, price_file: str | Path = PRICE_FILE) -> dict[str, Any]:
    template_to_profile = {
        "Momentum": "xmom",
        "Mean Reversion": "gaprev",
        "Catalyst": "sec8k",
        "PEAD": "pead",
        "Form 4 Cluster Buying": "form4",
        "LowVol Tradability": "lowvol",
        "Dollar-Bar Microstructure": "dollarbar",
        "Regime Filter": "regime",
        "PDUFA Run-Up": "sec8k",
        "13D Activist Follow-On": "form4",
    }
    story = build_strategy_chart_story(template_to_profile.get(str(manifest["template"]), "xmom"), price_file=price_file)
    story["title"] = f"Chart preview: {manifest['strategy_name']} on {story['symbol']}"
    story["explanation"] = manifest["chart_requirement"]
    labels = ["ENTRY: " + manifest["entry_rule"], "EXIT: " + manifest["exit_rule"], "GATE: " + manifest["first_gate"]]
    markers = story.get("markers", [])
    for index, label in enumerate(labels):
        if index < len(markers):
            markers[index]["label"] = label
    story["markers"] = markers
    return story


def validate_workbench_manifest(manifest: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    strategy_name = str(manifest.get("strategy_name", "")).strip()
    universe = str(manifest.get("universe", ""))
    template = str(manifest.get("template", ""))
    provider_allowed = bool(manifest.get("provider_query_allowed", False))
    required_data = [str(item).lower() for item in manifest.get("required_data", [])]
    cost_bps = int(manifest.get("cost_bps", 0))
    holding_period = int(manifest.get("holding_period_days", 0))

    rows.append(_validation_row("Named hypothesis", bool(strategy_name and strategy_name != "UNTITLED_STRATEGY"), "Strategy needs a stable ledger name."))
    rows.append(_validation_row("Cost model declared", cost_bps >= 0, f"{cost_bps} bps round-trip cost is part of the hypothesis."))
    rows.append(_validation_row("Holding period declared", holding_period > 0, f"{holding_period} days declared before any result is seen."))

    needs_external = any(token in " ".join(required_data) for token in ["event timestamp", "consensus eps", "fda", "schedule 13d", "sec form 4"])
    if needs_external and not provider_allowed:
        rows.append({"check": "Provider permission", "status": "BLOCK", "detail": f"{template} needs external/event data; provider query is not allowed."})
    else:
        rows.append({"check": "Provider permission", "status": "PASS", "detail": "No external query needed, or the query is explicitly allowed after a gate."})

    if "active-only" in universe:
        rows.append({"check": "Universe bias", "status": "WARN", "detail": "Active-only universe is exploratory and cannot promote without delisted/PIT coverage."})
    elif "custom universe pending" in universe:
        rows.append({"check": "Universe bias", "status": "BLOCK", "detail": "Custom universe must be validated before a controlled backtest."})
    else:
        rows.append({"check": "Universe bias", "status": "PASS", "detail": "Universe is compatible with a controlled local dry-run."})

    rows.append({"check": "Promotion lock", "status": "PASS", "detail": "Promotion remains false until all downstream gates pass."})
    return pd.DataFrame(rows)


def workbench_gate_is_valid(validation_rows: pd.DataFrame) -> bool:
    if validation_rows.empty or "status" not in validation_rows.columns:
        return False
    return not validation_rows["status"].astype(str).eq("BLOCK").any()


def build_workbench_pre_run_gate(manifest: dict[str, Any], validation_rows: pd.DataFrame) -> dict[str, Any]:
    return {
        "gate_id": "USER-STRATEGY-PRE-RUN-GATE-DRAFT",
        "strategy_name": manifest["strategy_name"],
        "template": manifest["template"],
        "provider_query_allowed": manifest["provider_query_allowed"],
        "promotion_allowed": False,
        "gate_valid": workbench_gate_is_valid(validation_rows),
        "checks": validation_rows.to_dict("records"),
        "blocked_actions": ["live_trading", "paper_trading", "promotion_without_final_decision"],
        "next_allowed_action": "controlled_local_dry_run" if workbench_gate_is_valid(validation_rows) else "fix_blocking_validation_rows",
    }


def build_controlled_backtest_preview(manifest: dict[str, Any], validation_rows: pd.DataFrame) -> dict[str, Any]:
    if not workbench_gate_is_valid(validation_rows):
        return {
            "status": "BLOCKED",
            "reason": "Validation panel contains blocking rows.",
            "trades": 0,
            "promotion_allowed": False,
        }
    base_score = max(0, 1000 - int(manifest["cost_bps"])) / 1000
    holding_penalty = min(int(manifest["holding_period_days"]), 180) / 360
    diagnostic_score = round(base_score - holding_penalty, 4)
    return {
        "status": "DRY_RUN_READY",
        "scope": "local preview only",
        "simulated_trades": 12,
        "diagnostic_score": diagnostic_score,
        "cost_bps": int(manifest["cost_bps"]),
        "promotion_allowed": False,
        "next_step": "Persist a real pre-run gate before connecting this to the backtest runner.",
    }


def _validation_row(check: str, passed: bool, detail: str) -> dict[str, str]:
    return {"check": check, "status": "PASS" if passed else "BLOCK", "detail": detail}


def build_strategy_chart_story(profile_key: str, *, price_file: str | Path = PRICE_FILE) -> dict[str, Any]:
    profile = next(item for item in STRATEGY_PROFILES if item.key == profile_key)
    prices = load_csv(Path(price_file))
    if prices.empty:
        return {
            "title": f"{profile.name} / no local price panel",
            "symbol": "",
            "prices": pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"]),
            "markers": [],
            "explanation": "No local OHLCV panel was available for this chart story.",
        }
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    symbol, preferred_date = _chart_seed(profile_key)
    if symbol not in set(prices["symbol"].astype(str)):
        symbol = str(prices["symbol"].iloc[0])
    symbol_prices = prices[prices["symbol"].astype(str) == symbol].sort_values("date").reset_index(drop=True)
    center = pd.Timestamp(preferred_date)
    if not ((symbol_prices["date"] - center).abs().min() <= pd.Timedelta(days=45)):
        center = symbol_prices.iloc[min(80, len(symbol_prices) - 1)]["date"]
    window = symbol_prices[(symbol_prices["date"] >= center - pd.Timedelta(days=45)) & (symbol_prices["date"] <= center + pd.Timedelta(days=45))].copy()
    if len(window) < 12:
        window = symbol_prices.head(min(60, len(symbol_prices))).copy()
    markers = _chart_markers(profile_key, window)
    return {
        "title": _chart_title(profile_key, profile.name, symbol),
        "symbol": symbol,
        "prices": window[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True),
        "markers": markers,
        "explanation": _chart_explanation(profile_key),
    }


def _chart_seed(profile_key: str) -> tuple[str, str]:
    seeds = {
        "xmom": ("CRMD", "2022-04-04"),
        "gaprev": ("CABA", "2022-07-28"),
        "sec8k": ("AEHR", "2023-01-06"),
        "pead": ("CRMD", "2024-05-09"),
        "lowvol": ("IOVA", "2022-05-04"),
        "form4": ("AEHR", "2023-03-31"),
        "dollarbar": ("ARRY", "2024-02-28"),
        "regime": ("IWM", "2024-08-05"),
    }
    return seeds.get(profile_key, ("AEHR", "2023-01-06"))


def _chart_markers(profile_key: str, prices: pd.DataFrame) -> list[dict[str, Any]]:
    if prices.empty:
        return []
    count = len(prices)
    buy_idx = min(max(count // 3, 0), count - 1)
    exit_idx = min(max((count * 2) // 3, 0), count - 1)
    block_idx = count - 1
    labels = {
        "xmom": ("BUY: top momentum candidate", "EXIT: 21d hold", "BLOCK: ex-top3 fragility"),
        "gaprev": ("WATCH: gap-down setup", "BUY: reclaim attempt", "BLOCK: cost realism"),
        "sec8k": ("EVENT: 8-K shock", "ORACLE: 09:45 tape read", "BLOCK: direction failed"),
        "pead": ("EVENT: earnings window", "NEED: SUE direction", "BLOCK: no PIT consensus"),
        "lowvol": ("FILTER: tradability pass", "BUY: low-vol basket", "BLOCK: negative net"),
        "form4": ("FILING: Form 4 scan", "NEED: cluster buy", "BLOCK: no events"),
        "dollarbar": ("TRANSFORM: dollar bars", "PROBE: micro-reversion", "BLOCK: net negative"),
        "regime": ("CLASSIFY: regime", "OVERLAY: risk rules", "MODE: diagnostics only"),
    }
    first, second, third = labels.get(profile_key, ("Signal", "Decision", "Gate"))
    return [
        _marker(prices.iloc[buy_idx], first, "buy"),
        _marker(prices.iloc[exit_idx], second, "exit"),
        _marker(prices.iloc[block_idx], third, "block"),
    ]


def _marker(row: pd.Series, label: str, kind: str) -> dict[str, Any]:
    return {
        "date": pd.Timestamp(row["date"]).date().isoformat(),
        "price": float(row["close"]),
        "label": label,
        "kind": kind,
    }


def _chart_title(profile_key: str, strategy_name: str, symbol: str) -> str:
    if profile_key == "pead":
        return f"{strategy_name}: why the chart is not enough ({symbol})"
    if profile_key in {"form4", "sec8k"}:
        return f"{strategy_name}: catalyst mapped onto price ({symbol})"
    return f"{strategy_name}: signal anatomy on {symbol}"


def _chart_explanation(profile_key: str) -> str:
    explanations = {
        "xmom": "The attractive section is not automatically alpha: the lab shows the apparent momentum depended on a few extreme winners.",
        "gaprev": "The buy zone only exists after RTH remapping. Daily gaps were rejected because they mixed pre-market and regular-session reality.",
        "sec8k": "The event produces volatility, but the opening tape did not supply a reliable long-only direction.",
        "pead": "A price reaction can illustrate the event, but the strategy remains blocked without point-in-time consensus surprise.",
        "lowvol": "The chart shows a tradable-looking segment, but the basket failed both gross/net and median gates.",
        "form4": "The visual idea is simple: buy after verified insider clusters. The tested universe produced no tradable cluster panel.",
        "dollarbar": "Dollar bars improved statistical stability, but the directional micro-reversion probe still failed after costs.",
        "regime": "This is no longer a buy/sell strategy: the chart shows how the lab now classifies context before allowing research actions.",
    }
    return explanations.get(profile_key, "The chart demonstrates the strategy logic and the governance gate that controlled it.")


def _match_strategy_rows(ledger: pd.DataFrame, profile: StrategyProfile) -> pd.DataFrame:
    if ledger.empty:
        return ledger
    haystack = (
        ledger.get("trial_id", pd.Series("", index=ledger.index)).astype(str)
        + " "
        + ledger.get("run_id", pd.Series("", index=ledger.index)).astype(str)
        + " "
        + ledger.get("decision", pd.Series("", index=ledger.index)).astype(str)
    ).str.upper()
    pattern = profile.decision_pattern.upper()
    if profile.key == "xmom":
        mask = haystack.str.contains("XMOM|MOMENTUM", regex=True)
    elif profile.key == "sec8k":
        mask = haystack.str.contains("SEC8K|SEC 8-K|SEC_8K", regex=True)
    else:
        mask = haystack.str.contains(pattern, regex=False)
    return ledger[mask].copy()
