from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any


@dataclass(frozen=True)
class MissionSection:
    label: str
    group: str
    description: str
    legacy_target: str


MISSION_SECTIONS: tuple[MissionSection, ...] = (
    MissionSection("Mission Brief", "Start here", "Cosa sta facendo il lab adesso.", "Command Center"),
    MissionSection("Project Story", "Start here", "Perche' esiste questa fortezza metodologica.", "Project Anatomy"),
    MissionSection("Strategy Builder", "Build", "Crea una strategia governata, una alla volta.", "Strategy Workbench"),
    MissionSection("Portfolio Lab", "Build", "Combina le strategie in basket diagnostici.", "Portfolio Lab"),
    MissionSection("Regime Playbook", "Build", "Quale famiglia funziona in quale regime.", "Results & Data"),
    MissionSection("Data Vault", "Audit", "Provider, blocker, copertura PIT e delisted.", "Results & Data"),
    MissionSection("Decision Ledger", "Audit", "Ogni decisione si'/no con la traccia degli artifact.", "Results & Data"),
)


def mission_section_by_label(label: str) -> MissionSection:
    for section in MISSION_SECTIONS:
        if section.label == label:
            return section
    return MISSION_SECTIONS[0]


def build_mission_status(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics", {}), dict) else {}
    readiness = payload.get("data_readiness", {}) if isinstance(payload.get("data_readiness", {}), dict) else {}
    current_regime = (
        payload.get("current_market_regime", {})
        if isinstance(payload.get("current_market_regime", {}), dict)
        else {}
    )
    readiness_status = str(readiness.get("status", "UNKNOWN"))
    blocker = (
        "DATA"
        if "DATA" in readiness_status or "MISSING" in readiness_status or "BLOCK" in readiness_status
        else "GOVERNANCE"
    )

    return {
        "mode": str(metrics.get("final_policy", "RISK_REGIME_ENGINE_ONLY")),
        "promoted": int(metrics.get("promoted_strategy_count", 0) or 0),
        "current_blocker": blocker,
        "current_regime": str(current_regime.get("regime_label", "UNKNOWN")),
        "next_gate": "Attach admissible data bundle" if blocker == "DATA" else "Review final decision gate",
        "plain_english_blocker": "Senza copertura PIT e delisted, ogni conclusione vera resta bloccata."
        if blocker == "DATA"
        else "La governance non consente promozione, paper trading o live trading.",
    }


def humanize_status_label(value: Any) -> str:
    return " ".join(str(value or "UNKNOWN").replace("_", " ").split()).title()


def mission_sidebar_html(active_label: str, status: dict[str, Any]) -> str:
    return (
        '<div class="mc-sidebar-shell">'
        '<div class="mc-brand">Adaptive Lab<span>Research operating system</span></div>'
        + '<div class="mc-status-card">'
        "<span>Current mode</span>"
        f'<strong>{escape(humanize_status_label(status.get("mode", "UNKNOWN")))}</strong>'
        f'<em>{escape(str(status.get("plain_english_blocker", "")))}</em>'
        f'<small>Promoted: {escape(str(status.get("promoted", 0)))} | Blocker: {escape(str(status.get("current_blocker", "UNKNOWN")))}</small>'
        f'<small>Next: {escape(str(status.get("next_gate", "Review gate")))}</small>'
        "</div></div>"
    )
