from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


EXECUTION_OUTPUTS_DIR = Path("experiments/provider_aware_research/execution_outputs")
FINAL_STATUS_DIR = EXECUTION_OUTPUTS_DIR / "LAB-FINAL-STATUS-PACK-RUN-001"
FIVE_POINT_DIR = EXECUTION_OUTPUTS_DIR / "TRANSITION-FIVE-POINT-BATCH-RUN-001"
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
LARGECAP_PRICE_FILE = Path("experiments/runs/20260508_173235_news_thr60/signals.csv")
WORKBENCH_OUTPUT_DIR = EXECUTION_OUTPUTS_DIR / "USER-STRATEGY-WORKBENCH"
DELISTED_DATA_SOURCE_GATE_DIR = Path("experiments/provider_aware_research/delisted_data_source_gate_20260525")
ORB_930_OUTPUT_DIR = EXECUTION_OUTPUTS_DIR / "ORB-930-CROSS-ASSET-BACKTEST-001"
WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS = {
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "IVV", "RSP", "XLK", "XLF", "XLE", "XLY", "XLP", "XLV", "XLI", "XLU", "XLB", "XLRE", "XLC",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "BRK.B", "JPM", "LLY", "V", "UNH", "XOM", "MA", "COST",
    "WMT", "NFLX", "PG", "JNJ", "HD", "ORCL", "ABBV", "BAC", "KO", "CRM", "CVX", "AMD", "MRK", "PEP", "TMO", "ADBE", "MCD", "CSCO",
    "GE", "LIN", "ABT", "QCOM", "IBM", "INTU", "DHR", "AMAT", "TXN", "CMCSA", "VZ", "NOW", "ISRG", "CAT", "PM", "DIS", "UBER", "GS",
    "RTX", "SPGI", "LOW", "PFE", "BKNG", "T", "HON", "NKE", "UNP", "COP", "MS", "LMT", "PLD", "DE", "ELV", "AMGN", "SYK", "ADP",
    "GILD", "C", "MDLZ", "PANW", "ADI", "MMC", "CB", "BMY", "SCHW", "SO", "UPS", "FI", "MU", "KLAC", "REGN", "ZTS", "EQIX", "APD",
    "ICE", "CME", "VRTX", "SNPS", "CDNS", "PGR", "AON", "HCA", "ETN", "MCO", "SHW", "BSX", "WM", "GD", "CL", "MCK", "TDG", "EOG",
}
WORKBENCH_CONFIGURED_SMALLCAP_SYMBOLS = {
    "AEHR", "ARRY", "CABA", "CRMD", "IOVA", "SAVA", "BLUE", "EDIT", "BEAM", "NTLA", "CRSP", "VERV", "FATE", "RLAY", "KYMR", "ADAP",
    "KURA", "VCYT", "TGTX", "IMTX", "ARVN", "CGEN", "VSTM", "XFOR", "KOD", "KPTI", "VYGR", "PDSB", "ADMA", "AKBA", "ALDX", "ALLO",
    "ANAB", "APLT", "AQST", "ARCT", "AUPH", "AXSM", "BCRX", "BNGO", "CERS", "CLDX", "CMPS", "CYTK", "DMTK", "DNLI", "EBS", "EYPT",
    "FGEN", "FOLD", "GERN", "GLUE", "HRTX", "IBRX", "INO", "KALA", "KNSA", "LQDA", "LXRX", "MCRB", "MIRM", "MRSN", "NERV", "NVAX",
    "OMER", "OPK", "PBYI", "PGEN", "PIRS", "PLRX", "PRTA", "PTGX", "RAPT", "RIGL", "RVNC", "SAGE", "SANA", "SNDX", "SRPT", "TERN",
    "TNGX", "TNYA", "TSVT", "VCEL", "VERA", "VKTX", "XENE", "XERS", "ZYME", "ZYXI", "BLFS", "CDNA", "CERT", "DCPH", "EOLS", "EVLO",
    "GH", "HCAT", "HLIT", "IRTC", "LUNG", "MODV", "NTRA", "OMCL", "PACB", "PGNY", "RARE", "RXRX", "SDGR", "TDOC", "TWST", "MARA",
    "RIOT", "HIMS", "UPST", "OPEN", "SOFI", "DNA", "IONQ", "RKLB", "ASTS", "JOBY", "ACHR", "ENVX", "QS", "CHPT", "BLNK", "RUN",
}
WORKBENCH_LARGECAP_ETF_SYMBOLS = WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS


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
        key="orb930",
        name="9:30 AM Opening Range Breakout",
        family="Cross-asset intraday",
        thesis="Mark the first 5m/15m New York range, trade the first breakout before 11:00, and exit by target, stop, or 16:00.",
        mechanism="Tests 5m and 15m opening ranges on gold, EUR/USD, and bitcoin with 1R, 3R, and 4R targets. Same-bar collisions are pessimistic, no-entry days stop at 11:00, and any open trade exits at the 16:00 New York session boundary.",
        demonstration=["09:30 NY anchor", "Opening range high/low", "Breakout before 11:00", "Stop opposite range", "1R/3R/4R target", "Median gate archive"],
        decision_pattern="ORB_930",
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
    "Custom Rule Builder": {
        "signal": "User-defined local rule over archived OHLCV features.",
        "entry_rule": "Enter windows selected by the chosen user signal and selection direction.",
        "exit_rule": "Exit after the declared holding period.",
        "failure_mode": "Overfitting, tiny local panels, and proxy-data misuse.",
        "required_data": ["daily OHLCV", "user rule manifest", "local price coverage"],
        "default_gate": "custom_rule_manifest_gate",
        "chart_hint": "The chart must show the custom signal window, entry candle, exit candle, and robustness gate.",
    },
    "9:30 AM ORB": {
        "signal": "Mark the first 5m or 15m New York opening range and trade the first breakout before 11:00.",
        "entry_rule": "Enter long on a 5m close above the opening-range high, or short on a 5m close below the opening-range low, before 11:00 ET.",
        "exit_rule": "Stop at the opposite side of the opening range; target at the frozen R multiple or exit at the session close.",
        "failure_mode": "Session anchoring ambiguity on 24h assets, false breakouts, and Yahoo intraday data limits.",
        "required_data": ["5m OHLCV", "America/New_York session mapping", "opening range high/low", "cost model"],
        "default_gate": "orb_session_mapping_gate",
        "chart_hint": "The chart must mark 09:30 opening range high/low, breakout close, stop, target, and 11:00 no-entry cutoff.",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


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
    orb_payload = orb_930_backtest_payload(root)
    if orb_payload["decision"]:
        orb_row = pd.DataFrame(
            [
                {
                    "trial_id": "ORB-930-CROSS-ASSET-BACKTEST-001",
                    "run_id": "ORB_930_CROSS_ASSET_BACKTEST",
                    "decision": orb_payload["decision"].get("decision", "UNKNOWN"),
                    "provider_query_performed": True,
                    "market_data_download_performed": True,
                    "backtest_performed": True,
                    "promotion_allowed": orb_payload["decision"].get("promotion_allowed", False),
                }
            ]
        )
        ledger = pd.concat([ledger, orb_row], ignore_index=True) if not ledger.empty else orb_row
    return {
        "ledger": ledger,
        "phase_summary": phase_summary,
        "operating_rules": operating_rules,
        "final_decision": final_decision,
        "regime_map": regime_map,
        "allocation": allocation,
        "smallcap_microstructure": smallcap_microstructure,
        "data_matrix": data_matrix,
        "orb_930": orb_payload,
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


def orb_930_backtest_payload(root: Path = Path(".")) -> dict[str, Any]:
    output_dir = root / ORB_930_OUTPUT_DIR
    decision = load_json(output_dir / "final_decision.json")
    summary = load_csv(output_dir / "summary.csv")
    trades = load_csv(output_dir / "trades.csv")
    report_path = output_dir / "orb_930_report.md"
    best = decision.get("best_configuration", {}) if decision else {}
    by_symbol = pd.DataFrame()
    if not trades.empty and "symbol" in trades.columns:
        by_symbol = trades.groupby("symbol", as_index=False).size().rename(columns={"size": "trades"})
    return {
        "available": bool(decision),
        "decision": decision,
        "summary": summary,
        "trades": trades,
        "by_symbol": by_symbol,
        "best": best,
        "report_path": str(report_path),
        "report_text": report_path.read_text(encoding="utf-8") if report_path.exists() else "",
    }


def delisted_data_source_gate_payload(root: Path = Path(".")) -> dict[str, Any]:
    gate_dir = root / DELISTED_DATA_SOURCE_GATE_DIR
    manifest = load_json(gate_dir / "delisted_data_source_gate_manifest.json")
    matrix = load_csv(gate_dir / "candidate_source_matrix.csv")
    requirements = load_csv(gate_dir / "pdufa_real_backtest_unlock_requirements.csv")
    decision_rule = load_csv(gate_dir / "source_decision_rule.csv")
    admissible = []
    if not matrix.empty and "gate_status" in matrix.columns:
        admissible = matrix[matrix["gate_status"].astype(str).str.lower().eq("admissible")]["provider"].astype(str).tolist()
    return {
        "manifest": manifest,
        "candidate_source_matrix": matrix,
        "unlock_requirements": requirements,
        "decision_rule": decision_rule,
        "admissible_sources": admissible,
    }


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
    strategy_mode: str = "Auto",
    custom_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = WORKBENCH_TEMPLATES.get(template, WORKBENCH_TEMPLATES["Momentum"])
    holding = int(holding_period_days)
    requested_mode = strategy_mode if strategy_mode in {"Auto", "Trading", "Investment"} else "Auto"
    analysis_mode = "Investment" if (requested_mode == "Investment" or (requested_mode == "Auto" and holding > 30)) else "Trading"
    normalized_custom_rules = _normalize_workbench_custom_rules(custom_rules)
    return {
        "strategy_name": name.strip() or "UNTITLED_STRATEGY",
        "template": template,
        "universe": universe,
        "holding_period_days": holding,
        "requested_mode": requested_mode,
        "analysis_mode": analysis_mode,
        "cost_bps": int(cost_bps),
        "provider_query_allowed": bool(allow_provider_query),
        "promotion_allowed": False,
        "custom_rules": normalized_custom_rules,
        "signal_contract": selected["signal"],
        "entry_rule": selected["entry_rule"],
        "exit_rule": selected["exit_rule"],
        "known_failure_mode": selected["failure_mode"],
        "required_data": selected["required_data"],
        "first_gate": selected["default_gate"],
        "chart_requirement": selected["chart_hint"],
        "next_step": "Generate a pre-run gate before any backtest or provider query.",
    }


def _normalize_workbench_custom_rules(custom_rules: dict[str, Any] | None) -> dict[str, Any]:
    rules = custom_rules or {}
    allowed_signals = {"momentum_21d", "momentum_5d", "dip_2d", "low_vol_5d", "volume_shock", "dollar_volume_shock"}
    allowed_filters = {"none", "positive_5d", "negative_5d", "volume_above_20d", "low_volatility_20d"}
    allowed_exits = {"holding_period", "risk_box"}
    signal = str(rules.get("signal", "momentum_21d")).strip().lower()
    if signal not in allowed_signals:
        signal = "momentum_21d"
    selection = str(rules.get("selection", "top")).strip().lower()
    if selection not in {"top", "bottom"}:
        selection = "top"
    try:
        entries_per_symbol = int(rules.get("entries_per_symbol", 20))
    except (TypeError, ValueError):
        entries_per_symbol = 20
    entries_per_symbol = max(1, min(200, entries_per_symbol))
    raw_allowed = rules.get("allowed_symbols", [])
    if isinstance(raw_allowed, str):
        allowed_symbols = [symbol.strip().upper() for symbol in raw_allowed.replace("\n", ",").split(",")]
    elif isinstance(raw_allowed, list):
        allowed_symbols = [str(symbol).strip().upper() for symbol in raw_allowed]
    else:
        allowed_symbols = []
    allowed_symbols = sorted({symbol for symbol in allowed_symbols if symbol})
    market_filter = str(rules.get("market_filter", "none")).strip().lower()
    if market_filter not in allowed_filters:
        market_filter = "none"
    exit_policy = str(rules.get("exit_policy", "holding_period")).strip().lower()
    if exit_policy not in allowed_exits:
        exit_policy = "holding_period"
    try:
        stop_loss_pct = float(rules.get("stop_loss_pct", 15))
    except (TypeError, ValueError):
        stop_loss_pct = 15.0
    try:
        take_profit_pct = float(rules.get("take_profit_pct", 30))
    except (TypeError, ValueError):
        take_profit_pct = 30.0
    stop_loss_pct = round(max(1.0, min(80.0, stop_loss_pct)), 2)
    take_profit_pct = round(max(1.0, min(500.0, take_profit_pct)), 2)
    return {
        "signal": signal,
        "selection": selection,
        "entries_per_symbol": entries_per_symbol,
        "allowed_symbols": allowed_symbols,
        "market_filter": market_filter,
        "exit_policy": exit_policy,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
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
        "9:30 AM ORB": "gaprev",
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
        "analysis_mode": manifest.get("analysis_mode", "Trading"),
        "provider_query_allowed": manifest["provider_query_allowed"],
        "promotion_allowed": False,
        "gate_valid": workbench_gate_is_valid(validation_rows),
        "checks": validation_rows.to_dict("records"),
        "blocked_actions": ["live_trading", "paper_trading", "promotion_without_final_decision"],
        "next_allowed_action": "controlled_local_dry_run" if workbench_gate_is_valid(validation_rows) else "fix_blocking_validation_rows",
    }


def workbench_manifest_signature(manifest: dict[str, Any]) -> str:
    signature_fields = {
        "strategy_name": manifest.get("strategy_name"),
        "template": manifest.get("template"),
        "universe": manifest.get("universe"),
        "holding_period_days": manifest.get("holding_period_days"),
        "requested_mode": manifest.get("requested_mode"),
        "analysis_mode": manifest.get("analysis_mode"),
        "cost_bps": manifest.get("cost_bps"),
        "provider_query_allowed": manifest.get("provider_query_allowed"),
        "signal_contract": manifest.get("signal_contract"),
        "entry_rule": manifest.get("entry_rule"),
        "exit_rule": manifest.get("exit_rule"),
        "first_gate": manifest.get("first_gate"),
        "custom_rules": manifest.get("custom_rules"),
    }
    payload = json.dumps(signature_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _validation_summary(validation_rows: pd.DataFrame) -> dict[str, int]:
    if validation_rows.empty or "status" not in validation_rows.columns:
        return {"pass": 0, "warn": 0, "block": 1}
    counts = validation_rows["status"].astype(str).str.upper().value_counts().to_dict()
    return {
        "pass": int(counts.get("PASS", 0)),
        "warn": int(counts.get("WARN", 0)),
        "block": int(counts.get("BLOCK", 0)),
    }


def build_controlled_backtest_preview(manifest: dict[str, Any], validation_rows: pd.DataFrame, *, price_file: str | Path = PRICE_FILE) -> dict[str, Any]:
    manifest_signature = workbench_manifest_signature(manifest)
    validation_summary = _validation_summary(validation_rows)
    data_scope_preview = build_workbench_data_scope_preview(manifest, price_file=price_file)
    base_report = {
        "manifest_signature": manifest_signature,
        "strategy_name": manifest["strategy_name"],
        "template": manifest["template"],
        "universe": manifest["universe"],
        "holding_period_days": int(manifest["holding_period_days"]),
        "requested_mode": manifest.get("requested_mode", "Auto"),
        "analysis_mode": manifest.get("analysis_mode", "Trading"),
        "cost_bps": int(manifest["cost_bps"]),
        "provider_query_allowed": bool(manifest["provider_query_allowed"]),
        "validation_summary": validation_summary,
        "data_scope_preview": data_scope_preview,
        "promotion_allowed": False,
    }
    if not workbench_gate_is_valid(validation_rows):
        return {
            **base_report,
            "status": "BLOCKED",
            "reason": "Validation panel contains blocking rows.",
            "trades": 0,
            "decision": "DRY_RUN_BLOCKED",
            "why": "The workbench refuses to simulate a strategy while any pre-run validation row is BLOCK.",
            "risk_notes": [
                "Fix the blocking rows before any local preview.",
                "No provider query, paper trade, live trade, or promotion is allowed from this state.",
            ],
            "next_actions": ["Resolve BLOCK checks", "Re-run the controlled dry-run on the updated manifest"],
            "dry_run_rows": validation_rows.to_dict("records"),
        }
    local_trades, local_summary = _build_local_workbench_trades(manifest, price_file=price_file)
    if not local_trades:
        return {
            **base_report,
            "status": "BLOCKED",
            "reason": "No local archived price rows were available for this manifest.",
            "trades": 0,
            "decision": "LOCAL_DRY_RUN_BLOCKED_NO_DATA",
            "why": "The workbench can only run a controlled local dry-run when the archived price panel has enough rows per symbol.",
            "risk_notes": ["No provider query was attempted.", "No synthetic trades were invented to fill the gap."],
            "next_actions": ["Attach a valid local price panel", "Re-run the controlled dry-run"],
            "dry_run_rows": [{"metric": "Local data", "value": "missing_or_insufficient", "interpretation": "The runner refused to fabricate trades."}],
        }
    gross_return_sum = round(sum(float(row["gross_return"]) for row in local_trades), 6)
    net_return_sum = round(sum(float(row["net_return"]) for row in local_trades), 6)
    average_net_return = round(net_return_sum / len(local_trades), 6)
    cost_drag = round(int(manifest["cost_bps"]) / 10000, 6)
    net_edge_proxy = average_net_return
    diagnostic_score = round(average_net_return * 100, 4)
    equity_curve = _build_workbench_equity_curve(local_trades)
    analysis_mode = str(manifest.get("analysis_mode", "Trading"))
    portfolio_diagnostics = _build_workbench_portfolio_diagnostics(local_trades, equity_curve, int(manifest["holding_period_days"]), analysis_mode)
    bias_warnings = _build_workbench_bias_warnings(manifest, local_summary, portfolio_diagnostics)
    robustness_panel = _build_workbench_robustness_panel(local_trades, int(manifest["cost_bps"]), analysis_mode=analysis_mode, portfolio_diagnostics=portfolio_diagnostics)
    automatic_verdict = _build_workbench_verdict(robustness_panel, validation_summary, analysis_mode=analysis_mode, portfolio_diagnostics=portfolio_diagnostics, bias_warnings=bias_warnings)
    markdown_report = _build_workbench_markdown_report(manifest, local_summary, robustness_panel, automatic_verdict, local_trades, portfolio_diagnostics, bias_warnings)
    visual_diagnostics = build_workbench_visual_diagnostics(
        {
            "trade_rows": local_trades,
            "equity_curve": equity_curve,
            "robustness_panel": robustness_panel,
            "automatic_verdict": automatic_verdict,
            "cost_breakdown": {
                "round_trip_cost_bps": int(manifest["cost_bps"]),
                "cost_drag_proxy": cost_drag,
                "gross_return_sum": gross_return_sum,
                "net_return_sum": net_return_sum,
                "average_net_return": average_net_return,
                "net_edge_proxy": net_edge_proxy,
            },
        }
    )
    decision = "DRY_RUN_READY"
    if validation_summary["warn"] > 0:
        decision = "LOCAL_DRY_RUN_COMPLETE_WITH_WARNINGS"
    else:
        decision = "LOCAL_DRY_RUN_COMPLETE_NO_PROMOTION"
    return {
        **base_report,
        "status": "DRY_RUN_READY",
        "scope": "local archived price runner",
        "simulated_trades": len(local_trades),
        "diagnostic_score": diagnostic_score,
        "decision": decision,
        "gross_edge_proxy": gross_return_sum,
        "cost_drag_proxy": cost_drag,
        "time_drag_proxy": 0,
        "net_edge_proxy": net_edge_proxy,
        "why": _workbench_why_text(manifest, automatic_verdict),
        "local_data_summary": local_summary,
        "trade_rows": local_trades,
        "equity_curve": equity_curve,
        "portfolio_diagnostics": portfolio_diagnostics,
        "bias_warnings": bias_warnings,
        "robustness_panel": robustness_panel,
        "automatic_verdict": automatic_verdict,
        "visual_diagnostics": visual_diagnostics,
        "markdown_report": markdown_report,
        "assumptions": [
            f"Template: {manifest['template']}",
            f"Universe: {manifest['universe']}",
            f"Analysis mode: {analysis_mode}",
            f"Holding period frozen before result: {manifest['holding_period_days']} days",
            f"Round-trip cost frozen before result: {manifest['cost_bps']} bps",
        ],
        "cost_breakdown": {
            "round_trip_cost_bps": int(manifest["cost_bps"]),
            "cost_drag_proxy": cost_drag,
            "gross_return_sum": gross_return_sum,
            "net_return_sum": net_return_sum,
            "average_net_return": average_net_return,
            "net_edge_proxy": net_edge_proxy,
        },
        "risk_notes": [
            "Dry-run uses archived local prices and simplified template rules.",
            "Event-heavy templates remain proxy simulations until real point-in-time event calendars are attached.",
            *[f"{warning['warning_id']}: {warning['message']}" for warning in bias_warnings],
            "Promotion remains false even when the dry-run is ready.",
            "A real backtest still requires a persisted pre-run gate and an approved runner.",
        ],
        "next_actions": [
            "Persist a real pre-run gate if this manifest is worth testing.",
            "Attach a real data source and backtest runner only after the gate exists.",
            "Review cost, sample-size, outlier, and PIT gates before any promotion decision.",
        ],
        "dry_run_rows": [
            {"metric": "Manifest signature", "value": manifest_signature, "interpretation": "Changes whenever name/template/universe/cost/holding/provider contract changes."},
            {"metric": "Validation PASS/WARN/BLOCK", "value": f"{validation_summary['pass']}/{validation_summary['warn']}/{validation_summary['block']}", "interpretation": "Any BLOCK disables the simulated run."},
            {"metric": "Local symbols", "value": local_summary["symbols"], "interpretation": "Symbols found in the archived price panel."},
            {"metric": "Gross return sum", "value": gross_return_sum, "interpretation": "Sum of local template-rule trade returns before costs."},
            {"metric": "Cost drag proxy", "value": cost_drag, "interpretation": "Cost model translated into a visible friction component."},
            {"metric": "Net return sum", "value": net_return_sum, "interpretation": "Local gross return sum after the declared round-trip cost model."},
            {"metric": "portfolio_diagnostics", "value": portfolio_diagnostics["mode"], "interpretation": "Portfolio-level diagnostics used when the strategy is evaluated as Investment/Convex Basket."},
        ],
        "next_step": "Persist a real pre-run gate before connecting this to the backtest runner.",
    }


def persist_workbench_run_bundle(
    manifest: dict[str, Any],
    validation_rows: pd.DataFrame,
    preview: dict[str, Any],
    *,
    root: Path = Path("."),
) -> dict[str, str]:
    signature = workbench_manifest_signature(manifest)
    artifact_dir = root / WORKBENCH_OUTPUT_DIR / signature
    artifact_dir.mkdir(parents=True, exist_ok=True)
    gate = build_workbench_pre_run_gate(manifest, validation_rows)
    manifest_path = artifact_dir / "strategy_manifest.json"
    gate_path = artifact_dir / "pre_run_gate.json"
    result_path = artifact_dir / "dry_run_result.json"
    trade_list_path = artifact_dir / "trade_list.csv"
    equity_curve_path = artifact_dir / "equity_curve.csv"
    markdown_report_path = artifact_dir / "dry_run_report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    gate_path.write_text(json.dumps(gate, indent=2, sort_keys=True), encoding="utf-8")
    result_path.write_text(json.dumps(_json_safe(preview), indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame(preview.get("trade_rows", [])).to_csv(trade_list_path, index=False)
    pd.DataFrame(preview.get("equity_curve", [])).to_csv(equity_curve_path, index=False)
    markdown_report_path.write_text(str(preview.get("markdown_report", "")), encoding="utf-8")
    return {
        "artifact_dir": str(artifact_dir),
        "manifest_path": str(manifest_path),
        "gate_path": str(gate_path),
        "result_path": str(result_path),
        "trade_list_path": str(trade_list_path),
        "equity_curve_path": str(equity_curve_path),
        "markdown_report_path": str(markdown_report_path),
    }


def build_workbench_strategy_package(manifest: dict[str, Any], validation_rows: pd.DataFrame, preview: dict[str, Any]) -> dict[str, Any]:
    signature = workbench_manifest_signature(manifest)
    gate = build_workbench_pre_run_gate(manifest, validation_rows)
    data_scope = build_workbench_data_scope_preview(manifest)
    readiness = build_workbench_backtest_readiness(manifest, validation_rows, preview)
    package_readme = "\n".join(
        [
            f"# Strategy Package: {manifest['strategy_name']}",
            "",
            "## Purpose",
            "",
            "This package is a governed bridge from Workbench dry-run to a future real backtest.",
            "It does not authorize paper trading, live trading, provider queries, or strategy promotion.",
            "",
            "## Current Status",
            "",
            f"- manifest_signature: `{signature}`",
            f"- template: `{manifest['template']}`",
            f"- analysis_mode: `{manifest.get('analysis_mode', 'Trading')}`",
            f"- readiness: `{readiness['overall_status']}`",
            f"- promotion_allowed: `false`",
            "",
            "## Required Next Step",
            "",
            readiness["next_user_action"],
            "",
            "## Files",
            "",
            "- `strategy_manifest.json`: frozen user hypothesis.",
            "- `pre_run_gate.json`: validation and blocked actions.",
            "- `data_contract.json`: required data, local coverage, and provider permissions.",
            "- `command_spec.json`: future runner contract; execution remains disabled.",
            "- `risk_policy.json`: cost, gate, and promotion rules.",
            "- `dry_run_report.md`: local diagnostic report.",
        ]
    )
    return {
        "strategy_manifest.json": manifest,
        "pre_run_gate.json": gate,
        "data_contract.json": {
            "manifest_signature": signature,
            "strategy_name": manifest["strategy_name"],
            "template": manifest["template"],
            "required_data": manifest.get("required_data", []),
            "universe": manifest.get("universe", ""),
            "data_scope": data_scope,
            "provider_query_allowed": bool(manifest.get("provider_query_allowed", False)),
            "raw_payload_retention_allowed": False,
            "pit_or_survivorship_warning": any("active-only" in str(manifest.get("universe", "")).lower() for _ in [0]),
            "missing_data_action": "block_real_backtest_or_mark_proxy_only",
        },
        "command_spec.json": {
            "manifest_signature": signature,
            "command_type": "future_governed_backtest_package",
            "module": "UNASSIGNED_UNTIL_PRE_RUN_GATE_COMMITTED",
            "arguments": [],
            "execution_allowed": False,
            "provider_query_allowed": bool(manifest.get("provider_query_allowed", False)),
            "forbidden_flags": ["--paper", "--live", "--promote", "--retain-raw-response", "--sweep"],
            "next_allowed_action": "commit_package_then_select_or_build_a_governed_runner",
        },
        "risk_policy.json": {
            "manifest_signature": signature,
            "analysis_mode": manifest.get("analysis_mode", "Trading"),
            "holding_period_days": int(manifest.get("holding_period_days", 0)),
            "round_trip_cost_bps": int(manifest.get("cost_bps", 0)),
            "first_gate": manifest.get("first_gate", ""),
            "promotion_allowed": False,
            "required_gates_before_promotion": [
                "data_quality_gate",
                "sample_size_gate",
                "cost_realism_gate",
                "outlier_dependency_gate",
                "median_or_portfolio_gate",
                "final_decision_gate",
            ],
            "paper_live_policy": "forbidden_from_workbench_package",
        },
        "README.md": package_readme,
        "dry_run_report.md": str(preview.get("markdown_report", "")),
    }


def persist_workbench_strategy_package(
    manifest: dict[str, Any],
    validation_rows: pd.DataFrame,
    preview: dict[str, Any],
    *,
    root: Path = Path("."),
) -> dict[str, Any]:
    signature = workbench_manifest_signature(manifest)
    package_dir = root / WORKBENCH_OUTPUT_DIR / signature / "strategy_package"
    package_dir.mkdir(parents=True, exist_ok=True)
    package = build_workbench_strategy_package(manifest, validation_rows, preview)
    files: dict[str, str] = {}
    for filename, payload in package.items():
        path = package_dir / filename
        if filename.endswith(".json"):
            path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        files[filename] = str(path)
    return {
        "package_dir": str(package_dir),
        "manifest_signature": signature,
        "files": files,
    }


def load_workbench_strategy_packages(*, root: Path = Path("."), limit: int = 12) -> list[dict[str, Any]]:
    output_root = root / WORKBENCH_OUTPUT_DIR
    if not output_root.exists():
        return []
    packages: list[dict[str, Any]] = []
    for package_dir in sorted(output_root.glob("*/strategy_package"), key=lambda path: path.stat().st_mtime, reverse=True):
        inspection = inspect_workbench_strategy_package(package_dir)
        manifest = inspection.get("manifest", {})
        command = inspection.get("command_spec", {})
        risk = inspection.get("risk_policy", {})
        packages.append(
            {
                "strategy_name": str(manifest.get("strategy_name", package_dir.parent.name)),
                "template": str(manifest.get("template", "unknown")),
                "analysis_mode": str(risk.get("analysis_mode", manifest.get("analysis_mode", "unknown"))),
                "status": inspection["status"],
                "execution_allowed": bool(command.get("execution_allowed", False)),
                "promotion_allowed": bool(risk.get("promotion_allowed", False)),
                "package_dir": str(package_dir),
                "manifest_signature": str(command.get("manifest_signature", package_dir.parent.name)),
            }
        )
        if len(packages) >= limit:
            break
    return packages


def inspect_workbench_strategy_package(package_dir: Path) -> dict[str, Any]:
    package_dir = Path(package_dir)
    filenames = [
        "strategy_manifest.json",
        "pre_run_gate.json",
        "data_contract.json",
        "command_spec.json",
        "risk_policy.json",
        "README.md",
        "dry_run_report.md",
    ]
    files_present = {filename: (package_dir / filename).exists() for filename in filenames}
    manifest = load_json(package_dir / "strategy_manifest.json")
    gate = load_json(package_dir / "pre_run_gate.json")
    data_contract = load_json(package_dir / "data_contract.json")
    command_spec = load_json(package_dir / "command_spec.json")
    risk_policy = load_json(package_dir / "risk_policy.json")
    readme = (package_dir / "README.md").read_text(encoding="utf-8") if (package_dir / "README.md").exists() else ""
    dry_report = (package_dir / "dry_run_report.md").read_text(encoding="utf-8") if (package_dir / "dry_run_report.md").exists() else ""
    readiness_rows = [
        {
            "check": "execution_allowed",
            "status": "PASS" if command_spec.get("execution_allowed") is False else "BLOCK",
            "detail": "Package inspection must not enable execution.",
        },
        {
            "check": "promotion_allowed",
            "status": "PASS" if risk_policy.get("promotion_allowed") is False and gate.get("promotion_allowed") is False else "BLOCK",
            "detail": "Promotion must stay locked in package inspector.",
        },
        {
            "check": "required_files",
            "status": "PASS" if all(files_present.values()) else "BLOCK",
            "detail": f"missing={[name for name, present in files_present.items() if not present]}",
        },
        {
            "check": "forbidden_flags",
            "status": "PASS" if {"--paper", "--live", "--promote"}.issubset(set(command_spec.get("forbidden_flags", []))) else "BLOCK",
            "detail": "Command spec must keep paper/live/promote forbidden.",
        },
    ]
    status = "READY_FOR_RUNNER_BUILD" if all(row["status"] == "PASS" for row in readiness_rows) else "PACKAGE_BLOCKED"
    return {
        "package_dir": str(package_dir),
        "status": status,
        "files_present": files_present,
        "readiness_rows": readiness_rows,
        "manifest": manifest,
        "pre_run_gate": gate,
        "data_contract": data_contract,
        "command_spec": command_spec,
        "risk_policy": risk_policy,
        "readme": readme,
        "dry_run_report": dry_report,
    }


def display_safe_records(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    safe_rows: list[dict[str, str]] = []
    for row in records:
        safe_row: dict[str, str] = {}
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                safe_row[str(key)] = json.dumps(_json_safe(value), sort_keys=True)
            else:
                safe_row[str(key)] = str(_json_safe(value))
        safe_rows.append(safe_row)
    return safe_rows


def build_workbench_result_summary(preview: dict[str, Any]) -> dict[str, str]:
    verdict = dict(preview.get("automatic_verdict", {}))
    cost_breakdown = dict(preview.get("cost_breakdown", {}))
    diagnostics = dict(preview.get("portfolio_diagnostics", {}))
    net_sum = float(cost_breakdown.get("net_return_sum", diagnostics.get("total_net_return", 0.0)) or 0.0)
    gross_sum = float(cost_breakdown.get("gross_return_sum", diagnostics.get("total_gross_return", 0.0)) or 0.0)
    trade_count = int(preview.get("simulated_trades", diagnostics.get("trade_count", 0)) or 0)
    blockers = list(verdict.get("blockers", []))
    primary_blocker = str(blockers[0]) if blockers else "none"
    decision = str(verdict.get("decision", preview.get("decision", "DRY_RUN_READY")))
    direction = "positive" if net_sum > 0 else "negative" if net_sum < 0 else "flat"
    net_percent = f"{net_sum * 100:.2f}%"
    gross_percent = f"{gross_sum * 100:.2f}%"
    if primary_blocker == "none":
        next_action = "Use this as a research candidate only after a real pre-run gate and data-quality review."
    elif primary_blocker == "trade_count_gate":
        next_action = "Increase breadth or attach more local history before trusting the result."
    elif primary_blocker == "outlier_dependency_gate":
        next_action = "Broaden the universe and inspect whether the result survives without the largest winners."
    elif primary_blocker == "cost_stress_gate":
        next_action = "Reduce execution friction, switch to a maker-style assumption, or discard the rule."
    else:
        next_action = "Inspect the blocking gate before changing parameters."
    plain_result = (
        f"The local dry-run produced a {direction} net sum of {net_percent} across {trade_count} trades "
        f"after costs, versus {gross_percent} gross before costs. Promotion remains locked false."
    )
    return {
        "headline": decision.replace("_", " ").title(),
        "plain_result": plain_result,
        "primary_blocker": primary_blocker,
        "next_best_action": next_action,
        "net_return_percent": net_percent,
        "gross_return_percent": gross_percent,
        "trade_count": str(trade_count),
    }


def load_workbench_strategy_cards(*, root: Path = Path("."), limit: int = 12) -> list[dict[str, Any]]:
    output_root = root / WORKBENCH_OUTPUT_DIR
    if not output_root.exists():
        return []
    cards: list[dict[str, Any]] = []
    for result_path in sorted(output_root.glob("*/dry_run_result.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        result = load_json(result_path)
        manifest = load_json(result_path.parent / "strategy_manifest.json")
        cost_breakdown = dict(result.get("cost_breakdown", {}))
        verdict = dict(result.get("automatic_verdict", {}))
        cards.append(
            {
                "strategy_name": str(result.get("strategy_name") or manifest.get("strategy_name") or result_path.parent.name),
                "template": str(result.get("template") or manifest.get("template") or "unknown"),
                "analysis_mode": str(result.get("analysis_mode") or manifest.get("analysis_mode") or "unknown"),
                "decision": str(verdict.get("decision", result.get("decision", "unknown"))),
                "simulated_trades": int(result.get("simulated_trades", 0) or 0),
                "net_return_sum": float(cost_breakdown.get("net_return_sum", 0.0) or 0.0),
                "artifact_dir": str(result_path.parent),
                "manifest_signature": str(result.get("manifest_signature", result_path.parent.name)),
            }
        )
        if len(cards) >= limit:
            break
    return cards


def build_workbench_comparison_table(cards: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for card in cards:
        net_return = float(card.get("net_return_sum", 0.0) or 0.0)
        rows.append(
            {
                "strategy_name": str(card.get("strategy_name", "")),
                "template": str(card.get("template", "")),
                "decision": str(card.get("decision", "")),
                "simulated_trades": int(card.get("simulated_trades", 0) or 0),
                "net_return_percent": round(net_return * 100, 2),
                "artifact_dir": str(card.get("artifact_dir", "")),
                "governance_note": "Promotion locked; compare diagnostics only.",
            }
        )
    if not rows:
        return pd.DataFrame(columns=["strategy_name", "template", "decision", "simulated_trades", "net_return_percent", "artifact_dir", "governance_note"])
    return pd.DataFrame(rows).sort_values(["net_return_percent", "simulated_trades"], ascending=[False, False]).reset_index(drop=True)


def build_workbench_data_scope_preview(manifest: dict[str, Any], *, price_file: str | Path = PRICE_FILE) -> dict[str, Any]:
    prices = _load_workbench_price_panel(manifest, price_file=price_file)
    configured_symbols = _configured_symbols_for_universe(str(manifest.get("universe", "")))
    if prices.empty or "symbol" not in prices.columns:
        return {
            "data_scope": "missing_local_price_panel",
            "scope_explanation": "No local price panel is available for this universe.",
            "selected_symbols": [],
            "rows": 0,
            "symbols": 0,
            "configured_symbols": len(configured_symbols),
            "local_price_symbols": 0,
            "price_file": str(price_file),
        }
    filtered, scope = _filter_prices_for_workbench_universe(prices, str(manifest.get("universe", "")))
    filtered = _apply_custom_symbol_filter(filtered, manifest)
    selected_symbols = sorted(str(symbol) for symbol in filtered["symbol"].unique()) if not filtered.empty else []
    return {
        "data_scope": scope["data_scope"],
        "scope_explanation": scope["scope_explanation"],
        "selected_symbols": selected_symbols,
        "rows": int(len(filtered)),
        "symbols": int(len(selected_symbols)),
        "configured_symbols": len(configured_symbols),
        "local_price_symbols": int(len(selected_symbols)),
        "price_file": str(price_file),
    }


def build_workbench_strategy_narrative(manifest: dict[str, Any], data_scope_preview: dict[str, Any]) -> dict[str, Any]:
    template = str(manifest.get("template", "Momentum"))
    holding = int(manifest.get("holding_period_days", 0))
    cost_bps = int(manifest.get("cost_bps", 0))
    mode = str(manifest.get("analysis_mode", "Trading"))
    custom_rules = _normalize_workbench_custom_rules(manifest.get("custom_rules", {}))
    signal_labels = {
        "momentum_21d": "21-day momentum",
        "momentum_5d": "5-day momentum",
        "dip_2d": "2-day dip",
        "low_vol_5d": "5-day low-volatility",
        "volume_shock": "volume shock",
        "dollar_volume_shock": "dollar-volume shock",
    }
    filter_labels = {
        "none": "no additional market filter",
        "positive_5d": "positive 5-day trend filter",
        "negative_5d": "negative 5-day stress filter",
        "volume_above_20d": "above-average 20-day volume filter",
        "low_volatility_20d": "below-median 20-day volatility filter",
    }
    if template == "Custom Rule Builder":
        direction = "highest" if custom_rules["selection"] == "top" else "lowest"
        plain_rule = (
            f"Buy the {direction}-ranked local windows by {signal_labels[custom_rules['signal']]} "
            f"for each routed symbol, capped at {custom_rules['entries_per_symbol']} windows per symbol, "
            f"with {filter_labels[custom_rules['market_filter']]}."
        )
    else:
        plain_rule = f"Buy according to the {template} contract: {manifest.get('entry_rule', '')}"
    exit_rule = f"Exit after {holding} calendar days using the frozen local dry-run holding period."
    if template == "Custom Rule Builder" and custom_rules["exit_policy"] == "risk_box":
        exit_rule = (
            f"Exit after {holding} calendar days, or earlier if the local window touches "
            f"{custom_rules['stop_loss_pct']:g}% stop loss or {custom_rules['take_profit_pct']:g}% take profit."
        )
    data_coverage = {
        "configured_symbols": int(data_scope_preview.get("configured_symbols", 0)),
        "local_price_symbols": int(data_scope_preview.get("local_price_symbols", data_scope_preview.get("symbols", 0))),
        "local_rows": int(data_scope_preview.get("rows", 0)),
        "selected_symbols": data_scope_preview.get("selected_symbols", []),
        "coverage_ratio": round(
            int(data_scope_preview.get("local_price_symbols", data_scope_preview.get("symbols", 0))) / max(1, int(data_scope_preview.get("configured_symbols", 0))),
            6,
        ),
    }
    guardrails = [
        f"Cost model is frozen at {cost_bps} bps round-trip before seeing the result.",
        f"Analysis mode is {mode}; promotion remains locked false.",
        "No provider query is allowed unless the manifest explicitly enables it and a pre-run gate exists.",
        "Missing local prices are reported as unavailable, never fabricated.",
    ]
    if "active-only" in str(manifest.get("universe", "")):
        guardrails.append("Active-only universes are exploratory because delisted/PIT coverage is incomplete.")
    return {
        "plain_english_rule": plain_rule,
        "exit_plain_english": exit_rule,
        "failure_plain_english": f"The first blocker is {manifest.get('first_gate')}: {manifest.get('known_failure_mode')}",
        "data_coverage": data_coverage,
        "guardrails": guardrails,
    }


def build_workbench_rule_flow(manifest: dict[str, Any]) -> list[dict[str, str]]:
    custom_rules = _normalize_workbench_custom_rules(manifest.get("custom_rules", {}))
    signal_labels = {
        "momentum_21d": "21-day momentum",
        "momentum_5d": "5-day momentum",
        "dip_2d": "2-day dip",
        "low_vol_5d": "5-day low-volatility",
        "volume_shock": "volume shock",
        "dollar_volume_shock": "dollar-volume shock",
    }
    filter_labels = {
        "none": "No additional market filter.",
        "positive_5d": "Require positive 5-day trend before ranking.",
        "negative_5d": "Require negative 5-day stress before ranking.",
        "volume_above_20d": "Require above-average 20-day volume.",
        "low_volatility_20d": "Require below-median 20-day volatility.",
    }
    if str(manifest.get("template")) == "Custom Rule Builder":
        signal = signal_labels.get(custom_rules["signal"], custom_rules["signal"])
        entry = f"Rank windows by {signal}; choose the {custom_rules['selection']} {custom_rules['entries_per_symbol']} per symbol."
        risk = (
            f"{custom_rules['stop_loss_pct']:g}% stop and {custom_rules['take_profit_pct']:g}% take profit."
            if custom_rules["exit_policy"] == "risk_box"
            else "No intratrade stop/take-profit in the local dry-run; horizon exit only."
        )
        exit_text = (
            "Exit at risk-box touch or holding horizon."
            if custom_rules["exit_policy"] == "risk_box"
            else f"Exit after {int(manifest.get('holding_period_days', 0))} days."
        )
        filter_text = filter_labels.get(custom_rules["market_filter"], custom_rules["market_filter"])
    else:
        entry = str(manifest.get("entry_rule", "Template entry rule."))
        filter_text = "Template-level filters only; no custom filter selected."
        risk = f"{int(manifest.get('cost_bps', 0))} bps cost model; template failure mode: {manifest.get('known_failure_mode', '')}"
        exit_text = str(manifest.get("exit_rule", "Template exit rule."))
    return [
        {"block": "Universe", "description": str(manifest.get("universe", ""))},
        {"block": "Signal", "description": str(manifest.get("signal", WORKBENCH_TEMPLATES.get(str(manifest.get("template")), {}).get("signal", "")))},
        {"block": "Filter", "description": filter_text},
        {"block": "Entry", "description": entry},
        {"block": "Risk", "description": risk},
        {"block": "Exit", "description": exit_text},
        {"block": "Gates", "description": f"First gate: {manifest.get('first_gate')}; promotion_allowed=false."},
    ]


def build_workbench_trade_annotation_story(manifest: dict[str, Any], preview: dict[str, Any], *, price_file: str | Path = PRICE_FILE) -> dict[str, Any]:
    trades = list(preview.get("trade_rows", []))
    if not trades:
        return {
            "available": False,
            "reason": "No dry-run trade rows available.",
            "prices": pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"]),
            "markers": [],
            "risk_box": {},
        }
    trade = sorted(trades, key=lambda row: abs(float(row.get("net_return", 0.0))), reverse=True)[0]
    prices = _load_workbench_price_panel(manifest, price_file=price_file)
    prices, _scope = _filter_prices_for_workbench_universe(prices, str(manifest.get("universe", "")))
    prices = _apply_custom_symbol_filter(prices, manifest)
    symbol = str(trade.get("symbol", "")).upper()
    symbol_prices = prices[prices["symbol"].astype(str).str.upper() == symbol].copy()
    if symbol_prices.empty:
        return {
            "available": False,
            "reason": f"No local price rows found for {symbol}.",
            "prices": pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"]),
            "markers": [],
            "risk_box": {},
        }
    symbol_prices["date"] = pd.to_datetime(symbol_prices["date"])
    entry_date = pd.Timestamp(str(trade["entry_date"]))
    exit_date = pd.Timestamp(str(trade["exit_date"]))
    window = symbol_prices[(symbol_prices["date"] >= entry_date - pd.Timedelta(days=8)) & (symbol_prices["date"] <= exit_date + pd.Timedelta(days=8))].copy()
    if len(window) < 4:
        window = symbol_prices.head(min(40, len(symbol_prices))).copy()
    entry_price = float(trade.get("entry_price", 0.0))
    exit_price = float(trade.get("exit_price", 0.0))
    risk_box: dict[str, float] = {"entry_price": round(entry_price, 6)}
    custom_rules = _normalize_workbench_custom_rules(manifest.get("custom_rules", {}))
    if custom_rules["exit_policy"] == "risk_box" and entry_price > 0:
        risk_box["stop_price"] = round(entry_price * (1 - float(custom_rules["stop_loss_pct"]) / 100), 6)
        risk_box["take_profit_price"] = round(entry_price * (1 + float(custom_rules["take_profit_pct"]) / 100), 6)
    return {
        "available": True,
        "title": f"Annotated dry-run trade: {symbol}",
        "symbol": symbol,
        "prices": window[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True),
        "markers": [
            {"date": entry_date.date().isoformat(), "price": entry_price, "label": f"ENTRY: {manifest.get('entry_rule', '')}", "kind": "entry"},
            {"date": exit_date.date().isoformat(), "price": exit_price, "label": f"EXIT: {trade.get('exit_reason', 'exit')} net={float(trade.get('net_return', 0.0)):.2%}", "kind": "exit"},
        ],
        "risk_box": risk_box,
        "trade": trade,
        "explanation": "This chart annotates one generated local dry-run trade so the user can inspect what the rule actually did on a real local price path.",
    }


def write_workbench_phase_report(*, root: Path = Path(".")) -> Path:
    output_dir = root / WORKBENCH_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "WORKBENCH-V2-PHASE-REPORT.md"
    path.write_text(
        "\n".join(
            [
                "# Strategy Workbench V2",
                "",
                "## Scope",
                "",
                "- Added composable rule flow blocks: Universe, Signal, Filter, Entry, Risk, Exit, Gates.",
                "- Added Chart Annotator for generated dry-run trades.",
                "- Added readiness, blueprint, and metric glossary surfaces.",
                "",
                "# Strategy Workbench V3",
                "",
                "## Scope",
                "",
                "- Added governed strategy package generation.",
                "- Package includes strategy manifest, pre-run gate, data contract, command spec, risk policy, README, and dry-run report.",
                "- Package generation remains non-executing and cannot authorize paper/live trading.",
                "- Added Package Inspector to review saved packages before building any real runner.",
                "",
                "## Governance",
                "",
                "- `promotion_allowed` remains false inside the Workbench.",
                "- Dry-runs remain local and diagnostic.",
                "- Real backtests still require a committed pre-run gate, data contract, and separate governed runner.",
                "- Strategy packages keep `execution_allowed=false` and `promotion_allowed=false`.",
                "- Package Inspector can mark a package ready for runner build, but not ready for execution.",
                "",
                "## Next Phase",
                "",
                "- Convert approved strategy blueprints into real pre-run gate packages.",
                "- Connect only selected strategies to real backtest runners after the gate exists.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def build_workbench_backtest_readiness(manifest: dict[str, Any], validation_rows: pd.DataFrame, preview: dict[str, Any] | None = None) -> dict[str, Any]:
    validation_summary = _validation_summary(validation_rows)
    data_scope = build_workbench_data_scope_preview(manifest)
    preview = preview or {}
    simulated_trades = int(preview.get("simulated_trades", 0) or 0)
    has_dry_run = bool(preview and preview.get("status") == "DRY_RUN_READY")
    provider_allowed = bool(manifest.get("provider_query_allowed", False))
    required_data = [str(item).lower() for item in manifest.get("required_data", [])]
    event_like = any(token in " ".join(required_data) for token in ["sec", "fda", "event", "earnings", "schedule", "form 4", "pdufa"])
    stages = [
        {
            "stage": "Manifest",
            "status": "PASS" if validation_summary["block"] == 0 else "BLOCK",
            "meaning": "The user idea has a stable name, frozen cost, holding period, universe, and first gate.",
            "next_step": "Fix validation rows first." if validation_summary["block"] else "Manifest can be dry-run locally.",
        },
        {
            "stage": "Local data",
            "status": "PASS" if int(data_scope.get("local_price_symbols", 0)) > 0 else "BLOCK",
            "meaning": f"{data_scope.get('local_price_symbols', 0)} local symbols and {data_scope.get('rows', 0)} OHLCV rows are available.",
            "next_step": "Attach a local price panel." if int(data_scope.get("local_price_symbols", 0)) == 0 else "Dry-run may use only these local rows.",
        },
        {
            "stage": "Dry-run",
            "status": "PASS" if has_dry_run else "WAIT",
            "meaning": "The local simulator produced an auditable preview." if has_dry_run else "No dry-run has been generated for this exact manifest yet.",
            "next_step": "Review robustness gates." if has_dry_run else "Press the controlled local dry-run button.",
        },
        {
            "stage": "Provider/data contract",
            "status": "WARN" if event_like and not provider_allowed else "PASS",
            "meaning": "Event strategies need an explicit provider gate before real data calls." if event_like else "This rule can be evaluated on local OHLCV unless the user adds external data.",
            "next_step": "Enable provider permission only after writing a real pre-run gate." if event_like and not provider_allowed else "Keep raw payload retention disabled unless a protocol says otherwise.",
        },
        {
            "stage": "Sample and robustness",
            "status": "PASS" if simulated_trades >= 30 else "WARN",
            "meaning": f"{simulated_trades} dry-run trades were generated. Below 30 remains weak evidence.",
            "next_step": "Increase universe/history before trusting robustness." if simulated_trades < 30 else "Inspect top-winner and cost-stress gates.",
        },
        {
            "stage": "Promotion",
            "status": "LOCKED",
            "meaning": "The workbench cannot promote, paper trade, or live trade.",
            "next_step": "Create a separate governed backtest runner if the dry-run is worth escalation.",
        },
    ]
    blocking = [stage for stage in stages if stage["status"] == "BLOCK"]
    warnings = [stage for stage in stages if stage["status"] in {"WARN", "WAIT"}]
    if blocking:
        overall = "BLOCKED_BEFORE_DRY_RUN"
        next_action = blocking[0]["next_step"]
    elif not has_dry_run:
        overall = "DRY_RUN_PENDING"
        next_action = "Run the controlled local dry-run for this exact manifest."
    elif warnings:
        overall = "DRY_RUN_READY_REAL_BACKTEST_LOCKED"
        next_action = warnings[0]["next_step"]
    else:
        overall = "REAL_BACKTEST_PREP_REQUIRED"
        next_action = "Write and commit a real pre-run gate before connecting a provider or runner."
    return {
        "overall_status": overall,
        "promotion_allowed": False,
        "stages": stages,
        "next_user_action": next_action,
    }


def build_workbench_strategy_blueprint(manifest: dict[str, Any], preview: dict[str, Any] | None = None) -> dict[str, Any]:
    data_scope = build_workbench_data_scope_preview(manifest)
    narrative = build_workbench_strategy_narrative(manifest, data_scope)
    preview = preview or {}
    return {
        "strategy_name": str(manifest.get("strategy_name", "")),
        "template": str(manifest.get("template", "")),
        "analysis_mode": str(manifest.get("analysis_mode", "Trading")),
        "what_the_user_built": narrative["plain_english_rule"],
        "how_it_exits": narrative["exit_plain_english"],
        "first_blocker": narrative["failure_plain_english"],
        "data_available": narrative["data_coverage"],
        "frozen_assumptions": {
            "holding_period_days": int(manifest.get("holding_period_days", 0)),
            "cost_bps": int(manifest.get("cost_bps", 0)),
            "provider_query_allowed": bool(manifest.get("provider_query_allowed", False)),
            "promotion_allowed": False,
        },
        "latest_dry_run": {
            "available": bool(preview),
            "decision": preview.get("automatic_verdict", {}).get("decision", preview.get("decision", "not_run")) if preview else "not_run",
            "simulated_trades": int(preview.get("simulated_trades", 0) or 0),
            "net_return_sum": preview.get("cost_breakdown", {}).get("net_return_sum") if preview else None,
        },
        "real_backtest_unlock": [
            "Commit a pre-run gate for this exact manifest signature.",
            "Attach the real data provider or approved local panel declared in the data contract.",
            "Run a separate governed backtest runner, not the UI dry-run.",
            "Archive final_decision.json with promotion_allowed=false unless all gates pass.",
        ],
    }


def build_workbench_metric_glossary(preview: dict[str, Any]) -> list[dict[str, str]]:
    cost = dict(preview.get("cost_breakdown", {}))
    diagnostics = dict(preview.get("portfolio_diagnostics", {}))
    verdict = dict(preview.get("automatic_verdict", {}))
    return [
        {
            "metric": "Net return sum",
            "value": str(cost.get("net_return_sum", diagnostics.get("total_net_return", "n/a"))),
            "plain_meaning": "Additive total of all local dry-run trades after the declared round-trip cost. 0.45 means roughly +45% additive, not guaranteed portfolio CAGR.",
        },
        {
            "metric": "Average net",
            "value": str(cost.get("average_net_return", "n/a")),
            "plain_meaning": "The average trade after costs. This can look good even when the typical trade is weak if a few winners dominate.",
        },
        {
            "metric": "Median / typical trade",
            "value": str(diagnostics.get("median_net_return", verdict.get("median_net_return", "see robustness table"))),
            "plain_meaning": "The middle trade in the distribution. The lab cares about this because it resists jackpot illusion better than the mean.",
        },
        {
            "metric": "Top winner contribution",
            "value": str(diagnostics.get("top_decile_contribution", "see chart")),
            "plain_meaning": "How much of the positive result comes from the biggest winners. High values mean the strategy may depend on rare outliers.",
        },
        {
            "metric": "Promotion allowed",
            "value": str(preview.get("promotion_allowed", False)),
            "plain_meaning": "Always false in the Workbench. A dry-run can teach, but it cannot authorize paper/live trading.",
        },
    ]


def build_workbench_visual_diagnostics(preview: dict[str, Any]) -> dict[str, Any]:
    trades = list(preview.get("trade_rows", []))
    equity_curve = list(preview.get("equity_curve", []))
    robustness_panel = dict(preview.get("robustness_panel", {}))
    verdict = dict(preview.get("automatic_verdict", {}))
    net_returns = [float(row.get("net_return", 0.0)) for row in trades]
    distribution = _workbench_trade_distribution(net_returns)
    positive_total = sum(value for value in net_returns if value > 0)
    top_winners: list[dict[str, Any]] = []
    for row in sorted(trades, key=lambda item: float(item.get("net_return", 0.0)), reverse=True)[:10]:
        net_return = round(float(row.get("net_return", 0.0)), 6)
        top_winners.append(
            {
                "symbol": row.get("symbol", ""),
                "entry_date": row.get("entry_date", ""),
                "exit_date": row.get("exit_date", ""),
                "net_return": net_return,
                "share_of_positive_net": round(net_return / positive_total, 6) if positive_total > 0 and net_return > 0 else 0.0,
            }
        )
    verdict_blocks = [
        {
            "gate": gate_name,
            "status": gate_payload.get("status"),
            "detail": gate_payload.get("detail"),
        }
        for gate_name, gate_payload in robustness_panel.items()
        if gate_payload.get("status") in {"BLOCK", "WARN", "INFO"}
    ]
    headline = str(verdict.get("decision", preview.get("decision", "DRY_RUN_READY")))
    blockers = verdict.get("blockers", [])
    warnings = verdict.get("warnings", [])
    if blockers:
        explanation = f"Blocked by {', '.join(blockers)}. The dry-run is useful diagnostically, but not promotable."
    elif warnings:
        explanation = f"Passed hard blockers with warnings: {', '.join(warnings)}. This is still not a promoted strategy."
    else:
        explanation = "No hard blocker fired in the local dry-run, but promotion remains false until a real governed backtest exists."
    return {
        "result_explainer": {
            "headline": headline,
            "explanation": explanation,
            "promotion_allowed": bool(verdict.get("promotion_allowed", False)),
        },
        "trade_distribution": distribution,
        "top_winners": top_winners,
        "equity_curve": equity_curve,
        "verdict_blocks": verdict_blocks,
    }


def _workbench_trade_distribution(net_returns: list[float]) -> list[dict[str, Any]]:
    if not net_returns:
        return []
    buckets = [
        ("<= -20%", None, -0.20),
        ("-20% to -10%", -0.20, -0.10),
        ("-10% to 0%", -0.10, 0.0),
        ("0% to 10%", 0.0, 0.10),
        ("10% to 25%", 0.10, 0.25),
        ("> 25%", 0.25, None),
    ]
    rows: list[dict[str, Any]] = []
    for label, lower, upper in buckets:
        count = 0
        for value in net_returns:
            lower_ok = True if lower is None else value > lower
            upper_ok = True if upper is None else value <= upper
            if lower_ok and upper_ok:
                count += 1
        rows.append({"bucket": label, "trade_count": count})
    return rows


def _build_local_workbench_trades(manifest: dict[str, Any], *, price_file: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prices = _load_workbench_price_panel(manifest, price_file=price_file)
    if prices.empty or not {"symbol", "date", "close"}.issubset(prices.columns):
        return [], {"symbols": 0, "rows": 0, "price_file": str(price_file)}
    prices = prices.copy()
    prices, scope = _filter_prices_for_workbench_universe(prices, str(manifest.get("universe", "")))
    prices = _apply_custom_symbol_filter(prices, manifest)
    configured_symbols = _configured_symbols_for_universe(str(manifest.get("universe", "")))
    custom_allowed_symbols = _custom_allowed_symbols(manifest)
    if prices.empty:
        return [], {
            "symbols": 0,
            "rows": 0,
            "price_file": str(price_file),
            "data_scope": scope["data_scope"],
            "scope_explanation": scope["scope_explanation"],
            "selected_symbols": [],
            "configured_symbols": len(configured_symbols),
            "local_price_symbols": 0,
            "custom_allowed_symbols": custom_allowed_symbols,
        }
    prices["date"] = pd.to_datetime(prices["date"])
    holding = max(1, int(manifest["holding_period_days"]))
    cost_return = round(int(manifest["cost_bps"]) / 10000, 6)
    entry_step = max(5, holding // 2)
    template_rule_profile = _workbench_template_rule_profile(str(manifest["template"]), manifest.get("custom_rules", {}))
    trades: list[dict[str, Any]] = []
    for symbol, group in prices.groupby("symbol"):
        symbol_prices = group.sort_values("date").reset_index(drop=True)
        if len(symbol_prices) <= holding + 1:
            continue
        for entry_index in _select_workbench_entry_indices(symbol_prices, str(manifest["template"]), holding, step=entry_step, custom_rules=manifest.get("custom_rules", {})):
            exit_index, exit_reason = _resolve_workbench_exit(symbol_prices, entry_index, holding, manifest)
            if exit_index <= entry_index:
                continue
            entry_price = float(symbol_prices.loc[entry_index, "close"])
            exit_price = float(symbol_prices.loc[exit_index, "close"])
            if entry_price <= 0:
                continue
            gross_return = round((exit_price / entry_price) - 1, 6)
            net_return = round(gross_return - cost_return, 6)
            trades.append(
                {
                    "symbol": str(symbol),
                    "entry_date": symbol_prices.loc[entry_index, "date"].date().isoformat(),
                    "exit_date": symbol_prices.loc[exit_index, "date"].date().isoformat(),
                    "entry_price": round(entry_price, 6),
                    "exit_price": round(exit_price, 6),
                    "gross_return": gross_return,
                    "cost_return": cost_return,
                    "net_return": net_return,
                    "holding_days": int((symbol_prices.loc[exit_index, "date"] - symbol_prices.loc[entry_index, "date"]).days),
                    "exit_reason": exit_reason,
                    "rule": str(manifest["template"]),
                    "template_rule_profile": template_rule_profile,
                    "entry_window_index": int(entry_index),
                }
            )
    summary = {
        "symbols": int(prices["symbol"].nunique()),
        "rows": int(len(prices)),
        "price_file": str(price_file),
        "eligible_trades": len(trades),
        "template_rule_profile": template_rule_profile,
        "data_scope": scope["data_scope"],
        "scope_explanation": scope["scope_explanation"],
        "selected_symbols": sorted(str(symbol) for symbol in prices["symbol"].unique()),
        "configured_symbols": len(configured_symbols),
        "local_price_symbols": int(prices["symbol"].nunique()),
        "custom_allowed_symbols": custom_allowed_symbols,
    }
    return trades, summary


def _load_workbench_price_panel(manifest: dict[str, Any], *, price_file: str | Path = PRICE_FILE) -> pd.DataFrame:
    universe = str(manifest.get("universe", "")).lower()
    explicit_file = Path(price_file)
    if explicit_file != PRICE_FILE:
        return _normalize_price_columns(load_csv(explicit_file))
    if "large-cap / etf" in universe and LARGECAP_PRICE_FILE.exists():
        return _normalize_price_columns(load_csv(LARGECAP_PRICE_FILE))
    if "expanded local research" in universe and LARGECAP_PRICE_FILE.exists():
        small = _normalize_price_columns(load_csv(PRICE_FILE))
        large = _normalize_price_columns(load_csv(LARGECAP_PRICE_FILE))
        return pd.concat([small, large], ignore_index=True)
    return _normalize_price_columns(load_csv(PRICE_FILE))


def _normalize_price_columns(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return prices
    rename_map = {column: column.lower().replace(" ", "_") for column in prices.columns}
    prices = prices.rename(columns=rename_map)
    if "date" not in prices.columns and "Date" in prices.columns:
        prices = prices.rename(columns={"Date": "date"})
    required = ["symbol", "date", "open", "high", "low", "close", "volume"]
    available = [column for column in required if column in prices.columns]
    normalized = prices[available].copy()
    for column in ["open", "high", "low", "close", "volume"]:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    if "symbol" in normalized.columns:
        normalized["symbol"] = normalized["symbol"].astype(str).str.upper()
    return normalized.dropna(subset=[column for column in ["symbol", "date", "close"] if column in normalized.columns])


def _filter_prices_for_workbench_universe(prices: pd.DataFrame, universe: str) -> tuple[pd.DataFrame, dict[str, str]]:
    symbols = prices["symbol"].astype(str).str.upper()
    if "large-cap / etf" in universe.lower():
        selected = prices[symbols.isin(WORKBENCH_LARGECAP_ETF_SYMBOLS)].copy()
        if selected["symbol"].nunique() < 3 and prices["symbol"].nunique() >= 3:
            fallback_symbols = (
                prices.assign(_symbol=prices["symbol"].astype(str))
                .groupby("_symbol")["volume"]
                .mean()
                .sort_values(ascending=False)
                .head(3)
                .index.tolist()
            )
            selected = prices[prices["symbol"].astype(str).isin(fallback_symbols)].copy()
            return selected, {
                "data_scope": "largecap_etf_broadened_demo_scope",
                "scope_explanation": "Local panel has fewer than 3 large-cap/ETF proxy symbols, so the preview broadens to the most liquid available symbols and remains non-promotable demo research.",
            }
        return selected, {
            "data_scope": "largecap_etf_clean_scope",
            "scope_explanation": "Uses only large-cap/ETF proxy symbols available in the local panel.",
        }
    if "small-cap active-only" in universe.lower():
        selected = prices[~symbols.isin(WORKBENCH_LARGECAP_ETF_SYMBOLS)].copy()
        return selected, {
            "data_scope": "smallcap_active_only_scope",
            "scope_explanation": "Uses active small-cap symbols only; results remain non-promotable without delisted/PIT coverage.",
        }
    if "expanded local research" in universe.lower():
        return prices.copy(), {
            "data_scope": "expanded_local_research_scope",
            "scope_explanation": "Combines every locally archived price panel available to increase breadth without making a provider query.",
        }
    if "local archived databento" in universe.lower():
        return prices.copy(), {
            "data_scope": "full_local_archived_panel",
            "scope_explanation": "Uses every symbol in the archived local Databento price panel.",
        }
    return prices.iloc[0:0].copy(), {
        "data_scope": "unresolved_custom_scope",
        "scope_explanation": "Custom universe has no approved local routing and must be validated first.",
    }


def _configured_symbols_for_universe(universe: str) -> set[str]:
    lowered = universe.lower()
    if "large-cap / etf" in lowered:
        return set(WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS)
    if "small-cap active-only" in lowered:
        return set(WORKBENCH_CONFIGURED_SMALLCAP_SYMBOLS)
    if "expanded local research" in lowered:
        return set(WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS) | set(WORKBENCH_CONFIGURED_SMALLCAP_SYMBOLS)
    if "local archived databento" in lowered:
        return {"AEHR", "ARRY", "CABA", "CRMD", "IOVA", "IWM"}
    return set()


def _custom_allowed_symbols(manifest: dict[str, Any]) -> list[str]:
    custom_rules = manifest.get("custom_rules", {})
    symbols = custom_rules.get("allowed_symbols", []) if isinstance(custom_rules, dict) else []
    return sorted({str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()})


def _apply_custom_symbol_filter(prices: pd.DataFrame, manifest: dict[str, Any]) -> pd.DataFrame:
    if str(manifest.get("template")) != "Custom Rule Builder":
        return prices
    allowed_symbols = _custom_allowed_symbols(manifest)
    if not allowed_symbols or prices.empty or "symbol" not in prices.columns:
        return prices
    return prices[prices["symbol"].astype(str).str.upper().isin(allowed_symbols)].copy()


def _select_workbench_entry_indices(symbol_prices: pd.DataFrame, template: str, holding: int, *, step: int, custom_rules: dict[str, Any] | None = None) -> list[int]:
    max_entry = max(0, len(symbol_prices) - holding - 1)
    if max_entry <= 1:
        return [1] if max_entry == 1 else []
    base_indices = list(range(1, max_entry + 1, step))
    close = symbol_prices["close"].astype(float)
    volume = symbol_prices["volume"].astype(float) if "volume" in symbol_prices.columns else pd.Series(1.0, index=symbol_prices.index)
    one_day_return = close.pct_change()
    two_day_return = close.pct_change(2)
    five_day_return = close.pct_change(5)
    ten_day_return = close.pct_change(10)
    twenty_one_day_return = close.pct_change(21)
    volatility = one_day_return.rolling(5).std()
    dollar_volume = close * volume
    volume_ratio = volume / volume.rolling(20, min_periods=3).mean()

    if template == "Custom Rule Builder":
        normalized = _normalize_workbench_custom_rules(custom_rules)
        signal = _custom_workbench_signal_series(symbol_prices, normalized["signal"])
        signal = _apply_custom_market_filter(symbol_prices, signal, normalized["market_filter"])
        return _ranked_entry_indices(signal, max_entry, base_indices, largest=normalized["selection"] == "top", limit=int(normalized["entries_per_symbol"]))
    if template == "Momentum":
        return _ranked_entry_indices(twenty_one_day_return, max_entry, base_indices, largest=True, limit=90)
    if template in {"Mean Reversion", "GapRev RTH Reversion"}:
        return _ranked_entry_indices(two_day_return, max_entry, base_indices, largest=False, limit=70)
    if template == "Catalyst":
        event_pressure = one_day_return.abs() * volume_ratio.fillna(1.0)
        return _ranked_entry_indices(event_pressure, max_entry, base_indices, largest=True, limit=55)
    if template == "PEAD":
        earnings_proxy = one_day_return.where(one_day_return > 0) * volume_ratio.fillna(1.0)
        return _ranked_entry_indices(earnings_proxy, max_entry, base_indices, largest=True, limit=45)
    if template == "Form 4 Cluster Buying":
        accumulation_proxy = five_day_return.where(five_day_return > 0) / volatility.replace(0, pd.NA)
        return _ranked_entry_indices(accumulation_proxy, max_entry, base_indices, largest=True, limit=35)
    if template == "LowVol Tradability":
        return _ranked_entry_indices(volatility, max_entry, base_indices, largest=False, limit=60)
    if template == "Dollar-Bar Microstructure":
        micro_reversion_proxy = dollar_volume.pct_change().where(one_day_return < 0)
        return _ranked_entry_indices(micro_reversion_proxy, max_entry, base_indices, largest=True, limit=65)
    if template == "Regime Filter":
        regime_proxy = ten_day_return.where(volatility <= volatility.rolling(60, min_periods=10).median())
        return _ranked_entry_indices(regime_proxy, max_entry, base_indices, largest=True, limit=50)
    if template == "PDUFA Run-Up":
        biotech_symbols = {"CABA", "CRMD", "IOVA"}
        if str(symbol_prices["symbol"].iloc[0]).upper() not in biotech_symbols:
            return []
        return _ranked_entry_indices(twenty_one_day_return.where(twenty_one_day_return > 0), max_entry, base_indices, largest=True, limit=40)
    if template == "13D Activist Follow-On":
        activist_proxy = twenty_one_day_return.where(volume_ratio > 1.15)
        return _ranked_entry_indices(activist_proxy, max_entry, base_indices, largest=True, limit=30)
    if template == "9:30 AM ORB":
        return _ranked_entry_indices((one_day_return.abs() * volume_ratio.fillna(1.0)), max_entry, base_indices, largest=True, limit=55)
    return base_indices


def _custom_workbench_signal_series(symbol_prices: pd.DataFrame, signal: str) -> pd.Series:
    close = symbol_prices["close"].astype(float)
    volume = symbol_prices["volume"].astype(float) if "volume" in symbol_prices.columns else pd.Series(1.0, index=symbol_prices.index)
    one_day_return = close.pct_change()
    if signal == "momentum_5d":
        return close.pct_change(5)
    if signal == "dip_2d":
        return close.pct_change(2)
    if signal == "low_vol_5d":
        return one_day_return.rolling(5).std()
    if signal == "volume_shock":
        return volume / volume.rolling(20, min_periods=3).mean()
    if signal == "dollar_volume_shock":
        dollar_volume = close * volume
        return dollar_volume / dollar_volume.rolling(20, min_periods=3).mean()
    return close.pct_change(21)


def _apply_custom_market_filter(symbol_prices: pd.DataFrame, signal: pd.Series, market_filter: str) -> pd.Series:
    close = symbol_prices["close"].astype(float)
    volume = symbol_prices["volume"].astype(float) if "volume" in symbol_prices.columns else pd.Series(1.0, index=symbol_prices.index)
    one_day_return = close.pct_change()
    five_day_return = close.pct_change(5)
    volatility = one_day_return.rolling(20, min_periods=5).std()
    mask = pd.Series(True, index=symbol_prices.index)
    if market_filter == "positive_5d":
        mask = five_day_return > 0
    elif market_filter == "negative_5d":
        mask = five_day_return < 0
    elif market_filter == "volume_above_20d":
        mask = volume > volume.rolling(20, min_periods=3).mean()
    elif market_filter == "low_volatility_20d":
        mask = volatility <= volatility.rolling(60, min_periods=10).median()
    return signal.where(mask)


def _resolve_workbench_exit(symbol_prices: pd.DataFrame, entry_index: int, holding: int, manifest: dict[str, Any]) -> tuple[int, str]:
    default_exit = min(entry_index + holding, len(symbol_prices) - 1)
    if str(manifest.get("template")) != "Custom Rule Builder":
        return default_exit, "holding_period"
    rules = _normalize_workbench_custom_rules(manifest.get("custom_rules", {}))
    if rules["exit_policy"] != "risk_box":
        return default_exit, "holding_period"
    entry_price = float(symbol_prices.loc[entry_index, "close"])
    if entry_price <= 0:
        return default_exit, "holding_period"
    stop_price = entry_price * (1 - (float(rules["stop_loss_pct"]) / 100))
    take_price = entry_price * (1 + (float(rules["take_profit_pct"]) / 100))
    for index in range(entry_index + 1, default_exit + 1):
        low = float(symbol_prices.loc[index, "low"]) if "low" in symbol_prices.columns else float(symbol_prices.loc[index, "close"])
        high = float(symbol_prices.loc[index, "high"]) if "high" in symbol_prices.columns else float(symbol_prices.loc[index, "close"])
        if low <= stop_price:
            return index, "stop_loss"
        if high >= take_price:
            return index, "take_profit"
    return default_exit, "holding_period"


def _ranked_entry_indices(series: pd.Series, max_entry: int, fallback: list[int], *, largest: bool, limit: int) -> list[int]:
    candidates = series.iloc[: max_entry + 1].replace([float("inf"), float("-inf")], pd.NA).dropna()
    if candidates.empty:
        return fallback
    ranked = candidates.nlargest(limit).index.tolist() if largest else candidates.nsmallest(limit).index.tolist()
    return sorted({max(1, min(int(candidate), max_entry)) for candidate in ranked})


def _workbench_template_rule_profile(template: str, custom_rules: dict[str, Any] | None = None) -> str:
    if template == "Custom Rule Builder":
        normalized = _normalize_workbench_custom_rules(custom_rules)
        return f"Custom Rule Builder:{normalized['signal']}:{normalized['selection']}:{normalized['market_filter']}:{normalized['exit_policy']}"
    if template in WORKBENCH_TEMPLATES:
        return template
    return "Momentum"


def _build_workbench_equity_curve(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    cumulative_gross = 0.0
    cumulative_net = 0.0
    peak_net = 0.0
    for index, trade in enumerate(sorted(trades, key=lambda row: (row["exit_date"], row["symbol"])), start=1):
        cumulative_gross = round(cumulative_gross + float(trade["gross_return"]), 6)
        cumulative_net = round(cumulative_net + float(trade["net_return"]), 6)
        peak_net = max(peak_net, cumulative_net)
        drawdown = round(cumulative_net - peak_net, 6)
        curve.append(
            {
                "step": index,
                "date": trade["exit_date"],
                "symbol": trade["symbol"],
                "cumulative_gross_return": cumulative_gross,
                "cumulative_net_return": cumulative_net,
                "drawdown": drawdown,
            }
        )
    return curve


def _build_workbench_portfolio_diagnostics(
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    holding_period_days: int,
    analysis_mode: str,
) -> dict[str, Any]:
    net_returns = sorted((float(row["net_return"]) for row in trades), reverse=True)
    gross_returns = [float(row["gross_return"]) for row in trades]
    winners = [value for value in net_returns if value > 0]
    losers = [value for value in net_returns if value <= 0]
    total_net = round(sum(net_returns), 6)
    total_gross = round(sum(gross_returns), 6)
    top1 = round(net_returns[0], 6) if net_returns else 0.0
    top3 = round(sum(net_returns[:3]), 6) if net_returns else 0.0
    top_decile_count = max(1, int(len(net_returns) * 0.1)) if len(net_returns) >= 10 else len(net_returns)
    top_decile = round(sum(net_returns[:top_decile_count]), 6) if net_returns else 0.0
    max_drawdown = round(min((float(row["drawdown"]) for row in equity_curve), default=0.0), 6)
    underwater_steps = sum(1 for row in equity_curve if float(row.get("drawdown", 0)) < 0)
    time_underwater_ratio = round(underwater_steps / len(equity_curve), 6) if equity_curve else 0.0
    average_winner = round(sum(winners) / len(winners), 6) if winners else 0.0
    average_loser = round(sum(losers) / len(losers), 6) if losers else 0.0
    payoff_ratio = round(average_winner / abs(average_loser), 6) if average_loser else None
    exit_year_returns: dict[str, float] = {}
    for trade in trades:
        year = str(trade["exit_date"])[:4]
        exit_year_returns[year] = round(exit_year_returns.get(year, 0.0) + float(trade["net_return"]), 6)
    positive_years = sum(1 for value in exit_year_returns.values() if value > 0)
    exposure_proxy = round((len(trades) * holding_period_days) / max(1, len({row["symbol"] for row in trades}) * 252), 6) if trades else 0.0
    top_decile_contribution = round(top_decile / total_net, 6) if total_net > 0 else None
    return {
        "mode": analysis_mode,
        "holding_period_days": int(holding_period_days),
        "trade_count": len(trades),
        "total_gross_return": total_gross,
        "total_net_return": total_net,
        "max_drawdown": max_drawdown,
        "time_underwater_ratio": time_underwater_ratio,
        "top1_contribution": top1,
        "top3_contribution": top3,
        "top_decile_contribution": top_decile_contribution,
        "top_decile_net_return": top_decile,
        "positive_years": positive_years,
        "year_count": len(exit_year_returns),
        "year_returns": exit_year_returns,
        "average_winner": average_winner,
        "average_loser": average_loser,
        "payoff_ratio": payoff_ratio,
        "exposure_proxy": exposure_proxy,
    }


def _build_workbench_bias_warnings(manifest: dict[str, Any], local_summary: dict[str, Any], portfolio_diagnostics: dict[str, Any]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    template = str(manifest.get("template", ""))
    universe = str(manifest.get("universe", "")).lower()
    mode = str(manifest.get("analysis_mode", "Trading"))
    event_templates = {"PDUFA Run-Up", "Form 4 Cluster Buying", "13D Activist Follow-On", "Catalyst", "PEAD"}
    proxy_scope = any(token in universe for token in ["active-only", "expanded local", "local archived"])
    drawdown = abs(float(portfolio_diagnostics.get("max_drawdown", 0.0)))
    total_net = float(portfolio_diagnostics.get("total_net_return", 0.0))
    if mode == "Investment" and template in event_templates and proxy_scope:
        warnings.append(
            {
                "warning_id": "SURVIVORSHIP_BIAS_SUSPECTED_HIGH",
                "severity": "high",
                "message": "Event-driven investment proxy uses local/active-style data without historical delisted issuers, so returns and drawdown may be artificially smooth.",
            }
        )
    if mode == "Investment" and total_net > 0 and drawdown > 0 and abs(total_net / drawdown) > 10:
        warnings.append(
            {
                "warning_id": "DRAWNDOWN_TOO_SMOOTH_FOR_EVENT_BASKET",
                "severity": "medium",
                "message": "Portfolio return is much larger than observed drawdown; this is plausible only after verifying delisted prices and PIT membership.",
            }
        )
    if str(local_summary.get("data_scope", "")).lower() in {"smallcap_active_only_scope", "expanded_local_research_scope", "full_local_archived_panel"}:
        warnings.append(
            {
                "warning_id": "PROXY_DATA_SCOPE_NOT_PROMOTABLE",
                "severity": "medium",
                "message": "The routed local scope is useful for UX and diagnostics but cannot promote a real strategy without a survivor-bias-free source gate.",
            }
        )
    return warnings


def _build_workbench_robustness_panel(
    trades: list[dict[str, Any]],
    cost_bps: int,
    *,
    analysis_mode: str = "Trading",
    portfolio_diagnostics: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    net_returns = sorted((float(row["net_return"]) for row in trades), reverse=True)
    gross_returns = [float(row["gross_return"]) for row in trades]
    trade_count = len(net_returns)
    net_sum = round(sum(net_returns), 6)
    ex_top1 = round(sum(net_returns[1:]), 6) if trade_count > 1 else 0.0
    ex_top3 = round(sum(net_returns[3:]), 6) if trade_count > 3 else 0.0
    trim_count = max(1, int(trade_count * 0.1)) if trade_count >= 100 else 0
    ex_top_decile = round(sum(net_returns[trim_count:]), 6) if trim_count else None
    median_return = round(float(pd.Series(net_returns).median()), 6) if net_returns else 0.0
    win_rate = round(sum(1 for value in net_returns if value > 0) / trade_count, 6) if trade_count else 0.0
    stressed_cost = round((cost_bps * 1.5) / 10000, 6)
    stressed_net_sum = round(sum(gross_returns) - (stressed_cost * trade_count), 6)
    outlier_status = "SKIP"
    outlier_mode = "sample_size_only"
    outlier_detail = "Sample below 10 trades: outlier removal would destroy too much of the panel."
    if 10 <= trade_count < 30:
        outlier_status = "PASS" if ex_top1 > 0 else "BLOCK"
        outlier_mode = "ex_top1"
        outlier_detail = "10-29 trades: only the single best trade is removed."
    elif 30 <= trade_count < 100:
        outlier_status = "PASS" if ex_top3 > 0 else "BLOCK"
        outlier_mode = "ex_top3"
        outlier_detail = "30-99 trades: removes the three best trades."
    elif trade_count >= 100:
        outlier_status = "PASS" if ex_top_decile is not None and ex_top_decile > 0 else "BLOCK"
        outlier_mode = "ex_top_decile"
        outlier_detail = "100+ trades: removes the top decile of trades."
    median_status = "PASS" if median_return > 0 else "BLOCK"
    win_rate_status = "PASS" if win_rate >= 0.5 else "BLOCK"
    median_detail = "Requires the typical trade, not only the average, to be positive."
    win_rate_detail = "Requires at least half the local trades to be positive."
    if analysis_mode == "Investment":
        median_status = "INFO"
        win_rate_status = "INFO"
        median_detail = "Investment/convex mode records median trade quality but does not reject only because the typical trade is negative."
        win_rate_detail = "Investment/convex mode records hit rate but does not require more than half of trades to win."
    panel = {
        "trade_count_gate": {
            "status": "PASS" if trade_count >= 30 else "BLOCK",
            "value": trade_count,
            "threshold": 30,
            "detail": "Requires at least 30 local trades before a research candidate label.",
        },
        "outlier_dependency_gate": {
            "status": outlier_status,
            "value": {"net_sum": net_sum, "ex_top1": ex_top1, "ex_top3": ex_top3, "ex_top_decile": ex_top_decile, "mode": outlier_mode},
            "detail": outlier_detail,
        },
        "median_return_gate": {
            "status": median_status,
            "value": median_return,
            "detail": median_detail,
        },
        "win_rate_gate": {
            "status": win_rate_status,
            "value": win_rate,
            "threshold": 0.5,
            "detail": win_rate_detail,
        },
        "cost_stress_gate": {
            "status": "PASS" if stressed_net_sum > 0 else "BLOCK",
            "value": {"stressed_cost_return": stressed_cost, "stressed_net_sum": stressed_net_sum},
            "detail": "Replays the trade list with 1.5x the declared round-trip cost.",
        },
    }
    if analysis_mode == "Investment" and portfolio_diagnostics is not None:
        total_net = float(portfolio_diagnostics.get("total_net_return", 0.0))
        top_decile_contribution = portfolio_diagnostics.get("top_decile_contribution")
        concentration_pass = top_decile_contribution is None or float(top_decile_contribution) <= 0.8
        panel["portfolio_total_return_gate"] = {
            "status": "PASS" if total_net > 0 else "BLOCK",
            "value": total_net,
            "detail": "Investment mode requires the whole local portfolio basket to be positive after costs.",
        }
        panel["convex_concentration_gate"] = {
            "status": "PASS" if concentration_pass else "WARN",
            "value": {
                "top_decile_contribution": top_decile_contribution,
                "top_decile_net_return": portfolio_diagnostics.get("top_decile_net_return"),
            },
            "detail": "Warns when the portfolio is mostly one cluster of jackpot trades rather than a repeatable basket.",
        }
    return panel


def _build_workbench_verdict(
    robustness_panel: dict[str, dict[str, Any]],
    validation_summary: dict[str, int],
    *,
    analysis_mode: str = "Trading",
    portfolio_diagnostics: dict[str, Any] | None = None,
    bias_warnings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if validation_summary["block"] > 0:
        decision = "DRY_RUN_BLOCKED"
    elif robustness_panel["trade_count_gate"]["status"] == "BLOCK":
        decision = "REJECTED_SAMPLE_TOO_SMALL"
    elif robustness_panel["outlier_dependency_gate"]["status"] == "BLOCK":
        decision = "REJECTED_OUTLIER_DEPENDENCY"
    elif robustness_panel["cost_stress_gate"]["status"] == "BLOCK":
        decision = "REJECTED_COST_STRESS"
    elif analysis_mode == "Investment" and robustness_panel.get("portfolio_total_return_gate", {}).get("status") == "BLOCK":
        decision = "REJECTED_NEGATIVE_PORTFOLIO"
    elif analysis_mode != "Investment" and (robustness_panel["median_return_gate"]["status"] == "BLOCK" or robustness_panel["win_rate_gate"]["status"] == "BLOCK"):
        decision = "REJECTED_WEAK_DISTRIBUTION"
    else:
        decision = "INVESTMENT_RESEARCH_CANDIDATE_ONLY" if analysis_mode == "Investment" else "RESEARCH_CANDIDATE_ONLY"
    blockers = [name for name, gate in robustness_panel.items() if gate.get("status") == "BLOCK"]
    warnings = [name for name, gate in robustness_panel.items() if gate.get("status") == "WARN"]
    summary = "Promotion remains disabled. This verdict only determines whether the dry-run deserves deeper research."
    if analysis_mode == "Investment":
        summary = "Promotion remains disabled. Investment mode judges the basket as a portfolio, so weak per-trade median or win rate is diagnostic rather than automatically fatal."
    if bias_warnings:
        warning_ids = ", ".join(warning["warning_id"] for warning in bias_warnings)
        summary = f"{summary} Bias status: PROXY_INVESTMENT_CANDIDATE_ONLY until warnings are resolved ({warning_ids})."
    return {
        "decision": decision,
        "promotion_allowed": False,
        "blockers": blockers,
        "warnings": warnings,
        "summary": summary,
    }


def _build_workbench_markdown_report(
    manifest: dict[str, Any],
    local_summary: dict[str, Any],
    robustness_panel: dict[str, dict[str, Any]],
    verdict: dict[str, Any],
    trades: list[dict[str, Any]],
    portfolio_diagnostics: dict[str, Any] | None = None,
    bias_warnings: list[dict[str, str]] | None = None,
) -> str:
    lines = [
        "# Workbench Dry-Run Report",
        "",
        f"Strategy: {manifest['strategy_name']}",
        f"Template: {manifest['template']}",
        f"Analysis mode: {manifest.get('analysis_mode', 'Trading')}",
        f"Universe: {manifest['universe']}",
        f"Data scope: {local_summary.get('data_scope', 'unknown')}",
        f"Selected symbols: {', '.join(local_summary.get('selected_symbols', [])) or 'none'}",
        "",
        "## Verdict",
        f"Decision: {verdict['decision']}",
        f"Promotion allowed: {verdict['promotion_allowed']}",
        f"Blockers: {', '.join(verdict['blockers']) or 'none'}",
        "",
        "## Robustness Gates",
    ]
    for name, gate in robustness_panel.items():
        lines.append(f"- {name}: {gate['status']} | {gate['value']}")
    if portfolio_diagnostics is not None:
        lines.extend(
            [
                "",
                "## Portfolio Diagnostics",
                f"- total_net_return: {portfolio_diagnostics['total_net_return']}",
                f"- max_drawdown: {portfolio_diagnostics['max_drawdown']}",
                f"- time_underwater_ratio: {portfolio_diagnostics['time_underwater_ratio']}",
                f"- top_decile_contribution: {portfolio_diagnostics['top_decile_contribution']}",
                f"- payoff_ratio: {portfolio_diagnostics['payoff_ratio']}",
            ]
        )
    if bias_warnings:
        lines.extend(["", "## Bias Warnings"])
        for warning in bias_warnings:
            lines.append(f"- {warning['warning_id']} ({warning['severity']}): {warning['message']}")
    lines.extend(["", "## Trades", f"Trade count: {len(trades)}"])
    for trade in trades[:10]:
        lines.append(f"- {trade['symbol']} {trade['entry_date']} -> {trade['exit_date']}: net {trade['net_return']}")
    return "\n".join(lines) + "\n"


def _workbench_why_text(manifest: dict[str, Any], verdict: dict[str, Any]) -> str:
    if manifest.get("analysis_mode") == "Investment":
        return (
            "The manifest passed the pre-run checks and was replayed as an investment/convex basket on archived local OHLCV. "
            "This mode treats low win rate and negative median trade as diagnostics, then asks whether the portfolio survives costs, drawdown, and jackpot concentration. "
            "No provider query was made, and event-heavy templates remain proxy tests until real point-in-time calendars are attached."
        )
    return "The manifest passed the pre-run checks and was replayed on the archived local OHLCV panel. No provider query was made."


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


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
        "orb930": ("CRMD", "2022-07-28"),
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
        "orb930": ("MARK: 09:30 range", "TRADE: first breakout", "BLOCK: median negative"),
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
        "orb930": "The chart illustrates the opening-range contract: mark the first range, wait for a breakout, then let stop/target decide. The real cross-asset run still failed the median gate.",
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
