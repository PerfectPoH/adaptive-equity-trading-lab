from dashboard.mission_control_ui import (
    MISSION_SECTIONS,
    build_mission_status,
    mission_section_by_label,
    mission_sidebar_html,
)


def test_mission_sections_are_beginner_readable() -> None:
    labels = [section.label for section in MISSION_SECTIONS]

    assert labels == [
        "Mission Brief",
        "Project Story",
        "Strategy Builder",
        "Portfolio Lab",
        "Regime Playbook",
        "Data Vault",
        "Decision Ledger",
    ]
    assert all(section.description for section in MISSION_SECTIONS)
    assert all(section.group in {"Start here", "Build", "Audit"} for section in MISSION_SECTIONS)


def test_mission_section_lookup_falls_back_to_brief() -> None:
    assert mission_section_by_label("Portfolio Lab").label == "Portfolio Lab"
    assert mission_section_by_label("Unknown").label == "Mission Brief"


def test_build_mission_status_translates_payload_to_plain_language() -> None:
    payload = {
        "metrics": {
            "promoted_strategy_count": 0,
            "final_policy": "RISK_REGIME_ENGINE_ONLY",
        },
        "current_market_regime": {
            "regime_label": "RANGE_NORMAL",
        },
        "data_readiness": {
            "status": "BLOCKED_TRUE_DATA_MISSING",
        },
    }

    status = build_mission_status(payload)

    assert status["mode"] == "RISK_REGIME_ENGINE_ONLY"
    assert status["promoted"] == 0
    assert status["current_blocker"] == "DATA"
    assert "PIT" in status["plain_english_blocker"]
    assert status["next_gate"] == "Attach admissible data bundle"


def test_mission_sidebar_html_contains_status_without_fake_navigation() -> None:
    html = mission_sidebar_html(
        active_label="Portfolio Lab",
        status={
            "mode": "RISK_REGIME_ENGINE_ONLY",
            "promoted": 0,
            "current_blocker": "DATA",
            "next_gate": "Attach admissible data bundle",
            "plain_english_blocker": "Missing PIT and delisted coverage.",
        },
    )

    assert "Adaptive Lab" in html
    assert "Attach admissible data bundle" in html
    assert "Portfolio Lab" not in html
    assert "Mission Brief" not in html
