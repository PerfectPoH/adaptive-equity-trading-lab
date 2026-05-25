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
