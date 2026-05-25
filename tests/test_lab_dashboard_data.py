from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    WORKBENCH_TEMPLATES,
    build_controlled_backtest_preview,
    build_workbench_chart_story,
    build_workbench_flow_nodes,
    build_workbench_manifest,
    build_workbench_pre_run_gate,
    build_workbench_data_scope_preview,
    persist_workbench_run_bundle,
    build_strategy_chart_story,
    classify_strategy_status,
    governance_metrics,
    load_dashboard_payload,
    project_capability_rows,
    project_lifecycle_rows,
    strategy_detail,
    strategy_rows,
    validate_workbench_manifest,
    workbench_gate_is_valid,
    workbench_manifest_signature,
)


def test_strategy_catalog_covers_core_research_tracks() -> None:
    keys = {profile.key for profile in STRATEGY_PROFILES}

    assert {"xmom", "gaprev", "sec8k", "pead", "lowvol", "form4", "dollarbar", "regime"}.issubset(keys)
    assert all(len(profile.demonstration) >= 5 for profile in STRATEGY_PROFILES)


def test_strategy_rows_groups_ledger_decisions_by_strategy_family() -> None:
    ledger = pd.DataFrame(
        [
            {"trial_id": "TRIAL-LOWVOL-TRADABILITY-001", "run_id": "LOWVOL", "decision": "LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM", "promotion_allowed": False},
            {"trial_id": "TRIAL-SEC8K-DIRECTION-001", "run_id": "SEC8K", "decision": "SEC8K_TAPE_ORACLE_ARCHIVE_CURRENT_FORM", "promotion_allowed": False},
            {"trial_id": "PEAD", "run_id": "PROBE", "decision": "BLOCKED_ALPHAVANTAGE_SOURCE_INSUFFICIENT", "promotion_allowed": False},
        ]
    )

    rows = strategy_rows(ledger).set_index("key")

    assert rows.loc["lowvol", "status"] == "ARCHIVED"
    assert rows.loc["sec8k", "runs"] == 1
    assert rows.loc["pead", "status"] == "BLOCKED"


def test_strategy_detail_exposes_demonstration_graph_edges() -> None:
    ledger = pd.DataFrame(
        [{"trial_id": "TRIAL-GAPREV-001", "run_id": "GAPREV", "decision": "TECHNICAL_CONTROLLED_RUN_COMPLETE__NO_PROMOTION", "promotion_allowed": False}]
    )

    detail = strategy_detail("gaprev", ledger)

    assert detail["profile"].name == "GapRev RTH Reversion"
    assert len(detail["flow_edges"]) == len(detail["flow_nodes"]) - 1
    assert detail["status"] == "ARCHIVED"


def test_classify_strategy_status_prioritizes_promotion_then_blockers() -> None:
    assert classify_strategy_status(["ANYTHING"], promoted=True) == "PROMOTED"
    assert classify_strategy_status(["BLOCKED_ALPHAVANTAGE_SOURCE_INSUFFICIENT"], promoted=False) == "BLOCKED"
    assert classify_strategy_status(["LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM"], promoted=False) == "ARCHIVED"
    assert classify_strategy_status([], promoted=False) == "NOT RUN"


def test_load_dashboard_payload_reads_final_status_artifacts(tmp_path: Path) -> None:
    final_dir = tmp_path / "experiments/provider_aware_research/execution_outputs/LAB-FINAL-STATUS-PACK-RUN-001"
    five_dir = tmp_path / "experiments/provider_aware_research/execution_outputs/TRANSITION-FIVE-POINT-BATCH-RUN-001"
    final_dir.mkdir(parents=True)
    five_dir.mkdir(parents=True)
    pd.DataFrame([{"trial_id": "A", "decision": "ARCHIVE", "promotion_allowed": False}]).to_csv(final_dir / "research_phase_closure_ledger.csv", index=False)
    (final_dir / "research_phase_summary.json").write_text(json.dumps({"decision_count": 1, "promoted_strategy_count": 0, "final_policy": "RISK_REGIME_ENGINE_ONLY"}), encoding="utf-8")
    (final_dir / "risk_regime_operating_rules.json").write_text(json.dumps({"mode": "RISK_REGIME_ENGINE"}), encoding="utf-8")
    (final_dir / "final_decision.json").write_text(json.dumps({"completed_points": 3}), encoding="utf-8")
    for filename in [
        "etf_largecap_regime_map.csv",
        "portfolio_allocation_smoke.csv",
        "smallcap_microstructure_diagnostic.csv",
        "data_upgrade_decision_matrix.csv",
    ]:
        pd.DataFrame([{"x": 1}]).to_csv(five_dir / filename, index=False)

    payload = load_dashboard_payload(tmp_path)
    metrics = governance_metrics(payload)

    assert metrics["decision_count"] == 1
    assert metrics["final_policy"] == "RISK_REGIME_ENGINE_ONLY"
    assert not payload["ledger"].empty


def test_project_capabilities_include_future_strategy_builder_as_planned() -> None:
    rows = project_capability_rows()

    assert "Future UX" in set(rows["area"])
    assert "planned" in set(rows["state"])


def test_project_lifecycle_documents_research_arc() -> None:
    rows = project_lifecycle_rows()

    assert len(rows) >= 6
    assert {"phase", "idea_source", "what_happened", "lesson"}.issubset(rows.columns)
    assert any(rows["phase"].str.contains("Momentum", case=False))
    assert any(rows["lesson"].str.contains("data", case=False))


def test_build_workbench_manifest_starts_unpromoted_and_gate_first() -> None:
    manifest = build_workbench_manifest(
        name="My gap probe",
        template="Mean Reversion",
        universe="small-cap active-only sandbox",
        holding_period_days=3,
        cost_bps=500,
        allow_provider_query=False,
    )

    assert "Mean Reversion" in WORKBENCH_TEMPLATES
    assert len(WORKBENCH_TEMPLATES) >= 10
    assert manifest["strategy_name"] == "My gap probe"
    assert manifest["promotion_allowed"] is False
    assert manifest["provider_query_allowed"] is False
    assert manifest["first_gate"] == "cost_realism_gate"
    assert manifest["entry_rule"]
    assert manifest["exit_rule"]
    assert manifest["chart_requirement"]
    assert "pre-run gate" in manifest["next_step"]

    flow_nodes = build_workbench_flow_nodes(manifest)
    assert flow_nodes[0] == "Template: Mean Reversion"
    assert "Data contract" in flow_nodes
    assert flow_nodes[-1] == "Pre-run manifest"

    validation = validate_workbench_manifest(manifest)
    assert workbench_gate_is_valid(validation)
    gate = build_workbench_pre_run_gate(manifest, validation)
    assert gate["gate_valid"] is True
    assert gate["next_allowed_action"] == "controlled_local_dry_run"
    preview = build_controlled_backtest_preview(manifest, validation)
    assert preview["status"] == "DRY_RUN_READY"
    assert preview["promotion_allowed"] is False
    assert preview["manifest_signature"] == workbench_manifest_signature(manifest)
    assert preview["strategy_name"] == "My gap probe"
    assert preview["template"] == "Mean Reversion"
    assert preview["validation_summary"]["block"] == 0
    assert preview["cost_breakdown"]["round_trip_cost_bps"] == 500
    assert preview["risk_notes"]
    assert preview["next_actions"]
    assert any(row["metric"] == "Manifest signature" for row in preview["dry_run_rows"])


def test_workbench_blocks_external_event_template_without_provider_permission() -> None:
    manifest = build_workbench_manifest(
        name="No provider catalyst",
        template="Catalyst",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=5,
        cost_bps=250,
        allow_provider_query=False,
    )

    validation = validate_workbench_manifest(manifest)
    gate = build_workbench_pre_run_gate(manifest, validation)
    preview = build_controlled_backtest_preview(manifest, validation)

    assert not workbench_gate_is_valid(validation)
    assert "BLOCK" in set(validation["status"])
    assert gate["next_allowed_action"] == "fix_blocking_validation_rows"
    assert preview["status"] == "BLOCKED"
    assert preview["decision"] == "DRY_RUN_BLOCKED"
    assert preview["validation_summary"]["block"] >= 1
    assert preview["dry_run_rows"]


def test_workbench_signature_and_preview_change_when_strategy_changes() -> None:
    first = build_workbench_manifest(
        name="Version one",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=21,
        cost_bps=500,
        allow_provider_query=False,
    )
    second = build_workbench_manifest(
        name="Version two",
        template="Mean Reversion",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=5,
        cost_bps=250,
        allow_provider_query=False,
    )

    first_validation = validate_workbench_manifest(first)
    second_validation = validate_workbench_manifest(second)
    first_preview = build_controlled_backtest_preview(first, first_validation)
    second_preview = build_controlled_backtest_preview(second, second_validation)

    assert workbench_manifest_signature(first) != workbench_manifest_signature(second)
    assert first_preview["manifest_signature"] != second_preview["manifest_signature"]
    assert first_preview["template"] == "Momentum"
    assert second_preview["template"] == "Mean Reversion"
    assert first_preview["strategy_name"] == "Version one"
    assert second_preview["strategy_name"] == "Version two"


def test_workbench_dry_run_uses_local_prices_and_returns_trade_artifacts(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "date": "2026-01-01", "open": 10.0, "high": 10.2, "low": 9.8, "close": 10.0, "volume": 1000},
            {"symbol": "AAA", "date": "2026-01-02", "open": 10.0, "high": 10.8, "low": 9.9, "close": 10.7, "volume": 1200},
            {"symbol": "AAA", "date": "2026-01-05", "open": 10.7, "high": 11.2, "low": 10.6, "close": 11.0, "volume": 1300},
            {"symbol": "AAA", "date": "2026-01-06", "open": 11.0, "high": 11.8, "low": 10.9, "close": 11.6, "volume": 1600},
            {"symbol": "BBB", "date": "2026-01-01", "open": 20.0, "high": 20.4, "low": 19.7, "close": 20.0, "volume": 900},
            {"symbol": "BBB", "date": "2026-01-02", "open": 20.0, "high": 20.1, "low": 19.0, "close": 19.2, "volume": 1500},
            {"symbol": "BBB", "date": "2026-01-05", "open": 19.2, "high": 19.6, "low": 18.9, "close": 19.5, "volume": 1400},
            {"symbol": "BBB", "date": "2026-01-06", "open": 19.5, "high": 20.0, "low": 19.4, "close": 19.8, "volume": 1100},
        ]
    ).to_csv(prices, index=False)
    manifest = build_workbench_manifest(
        name="Real local runner",
        template="Momentum",
        universe="local archived Databento panel",
        holding_period_days=2,
        cost_bps=100,
        allow_provider_query=False,
    )
    validation = validate_workbench_manifest(manifest)

    preview = build_controlled_backtest_preview(manifest, validation, price_file=prices)

    assert preview["scope"] == "local archived price runner"
    assert preview["simulated_trades"] == 2
    assert preview["trade_rows"]
    assert preview["equity_curve"]
    assert preview["local_data_summary"]["symbols"] == 2
    assert preview["local_data_summary"]["data_scope"] == "full_local_archived_panel"
    assert preview["cost_breakdown"]["net_return_sum"] == sum(row["net_return"] for row in preview["trade_rows"])
    assert preview["robustness_panel"]["trade_count_gate"]["status"] in {"PASS", "BLOCK"}
    assert preview["robustness_panel"]["outlier_dependency_gate"]["status"] in {"PASS", "BLOCK", "SKIP"}
    assert preview["robustness_panel"]["win_rate_gate"]["value"] >= 0
    assert preview["automatic_verdict"]["promotion_allowed"] is False
    assert preview["automatic_verdict"]["decision"] in {
        "RESEARCH_CANDIDATE_ONLY",
        "REJECTED_SAMPLE_TOO_SMALL",
        "REJECTED_OUTLIER_DEPENDENCY",
        "REJECTED_COST_STRESS",
        "REJECTED_WEAK_DISTRIBUTION",
    }
    assert {"cumulative_gross_return", "cumulative_net_return", "drawdown"}.issubset(preview["equity_curve"][0])
    assert "# Workbench Dry-Run Report" in preview["markdown_report"]


def test_workbench_universe_routes_to_distinct_price_scopes(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    rows = []
    for symbol, base in [("AEHR", 10.0), ("ARRY", 20.0), ("IWM", 100.0)]:
        for offset in range(6):
            rows.append(
                {
                    "symbol": symbol,
                    "date": f"2026-01-0{offset + 1}",
                    "open": base + offset,
                    "high": base + offset + 0.5,
                    "low": base + offset - 0.5,
                    "close": base + offset,
                    "volume": 1000 + offset,
                }
            )
    pd.DataFrame(rows).to_csv(prices, index=False)
    large = build_workbench_manifest(
        name="Large scope",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=2,
        cost_bps=100,
        allow_provider_query=False,
    )
    small = build_workbench_manifest(
        name="Small scope",
        template="Momentum",
        universe="small-cap active-only exploratory sandbox",
        holding_period_days=2,
        cost_bps=100,
        allow_provider_query=False,
    )

    large_preview = build_controlled_backtest_preview(large, validate_workbench_manifest(large), price_file=prices)
    small_preview = build_controlled_backtest_preview(small, validate_workbench_manifest(small), price_file=prices)

    assert large_preview["local_data_summary"]["data_scope"] == "largecap_etf_broadened_demo_scope"
    assert small_preview["local_data_summary"]["data_scope"] == "smallcap_active_only_scope"
    assert large_preview["local_data_summary"]["selected_symbols"] == ["AEHR", "ARRY", "IWM"]
    assert small_preview["local_data_summary"]["selected_symbols"] == ["AEHR", "ARRY"]
    assert large_preview["simulated_trades"] != small_preview["simulated_trades"]
    assert large_preview["data_scope_preview"]["selected_symbols"] == ["AEHR", "ARRY", "IWM"]
    assert small_preview["data_scope_preview"]["selected_symbols"] == ["AEHR", "ARRY"]


def test_workbench_default_largecap_scope_uses_expanded_local_artifact() -> None:
    manifest = build_workbench_manifest(
        name="Expanded large local",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )

    scope = build_workbench_data_scope_preview(manifest)
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    assert scope["data_scope"] == "largecap_etf_clean_scope"
    assert scope["symbols"] >= 10
    assert preview["simulated_trades"] >= 300
    assert preview["robustness_panel"]["outlier_dependency_gate"]["value"]["mode"] in {"ex_top_decile", "ex_top3"}


def test_workbench_expanded_local_research_scope_combines_local_panels() -> None:
    manifest = build_workbench_manifest(
        name="Expanded all local",
        template="Momentum",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )

    scope = build_workbench_data_scope_preview(manifest)
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    assert scope["data_scope"] == "expanded_local_research_scope"
    assert scope["symbols"] >= 15
    assert preview["simulated_trades"] >= 400


def test_persist_workbench_run_bundle_writes_manifest_gate_and_result(tmp_path: Path) -> None:
    manifest = build_workbench_manifest(
        name="Persisted strategy",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=2,
        cost_bps=100,
        allow_provider_query=False,
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)

    bundle = persist_workbench_run_bundle(manifest, validation, preview, root=tmp_path)

    assert bundle["artifact_dir"].startswith(str(tmp_path))
    assert Path(bundle["manifest_path"]).exists()
    assert Path(bundle["gate_path"]).exists()
    assert Path(bundle["result_path"]).exists()
    assert Path(bundle["trade_list_path"]).exists()
    assert Path(bundle["markdown_report_path"]).exists()


def test_build_strategy_chart_story_uses_real_ohlc_window(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {"symbol": "AEHR", "date": "2026-01-01", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1000},
            {"symbol": "AEHR", "date": "2026-01-02", "open": 10.2, "high": 11.0, "low": 10.1, "close": 10.8, "volume": 2000},
            {"symbol": "AEHR", "date": "2026-01-05", "open": 10.8, "high": 11.2, "low": 10.0, "close": 10.1, "volume": 3000},
            {"symbol": "AEHR", "date": "2026-01-06", "open": 10.1, "high": 10.4, "low": 9.9, "close": 10.0, "volume": 1500},
        ]
    ).to_csv(prices, index=False)

    story = build_strategy_chart_story("xmom", price_file=prices)

    assert story["symbol"] == "AEHR"
    assert {"date", "open", "high", "low", "close", "volume"}.issubset(story["prices"].columns)
    assert len(story["markers"]) >= 2
    assert any(marker["kind"] == "buy" for marker in story["markers"])
    assert story["title"]


def test_build_workbench_chart_story_relabels_markers_with_manifest_rules(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {"symbol": "CABA", "date": "2026-01-01", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1000},
            {"symbol": "CABA", "date": "2026-01-02", "open": 10.2, "high": 11.0, "low": 10.1, "close": 10.8, "volume": 2000},
            {"symbol": "CABA", "date": "2026-01-05", "open": 10.8, "high": 11.2, "low": 10.0, "close": 10.1, "volume": 3000},
            {"symbol": "CABA", "date": "2026-01-06", "open": 10.1, "high": 10.4, "low": 9.9, "close": 10.0, "volume": 1500},
        ]
    ).to_csv(prices, index=False)
    manifest = build_workbench_manifest(
        name="Reversion preview",
        template="Mean Reversion",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=3,
        cost_bps=500,
        allow_provider_query=False,
    )

    story = build_workbench_chart_story(manifest, price_file=prices)

    assert story["title"].startswith("Chart preview")
    assert story["markers"][0]["label"].startswith("ENTRY:")
    assert story["markers"][1]["label"].startswith("EXIT:")
    assert story["markers"][2]["label"].startswith("GATE:")
