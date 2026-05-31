from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS,
    WORKBENCH_CONFIGURED_SMALLCAP_SYMBOLS,
    WORKBENCH_TEMPLATES,
    build_controlled_backtest_preview,
    build_workbench_chart_story,
    build_workbench_rule_flow,
    build_workbench_trade_annotation_story,
    build_workbench_flow_nodes,
    build_workbench_manifest,
    build_workbench_pre_run_gate,
    build_workbench_backtest_readiness,
    build_workbench_strategy_package,
    build_workbench_comparison_table,
    build_workbench_data_scope_preview,
    build_workbench_result_summary,
    build_workbench_strategy_narrative,
    build_workbench_strategy_blueprint,
    build_workbench_metric_glossary,
    build_workbench_visual_diagnostics,
    build_portfolio_lab_preview,
    build_strategy_factory_components,
    build_portfolio_preregistration_draft,
    display_safe_records,
    delisted_data_source_gate_payload,
    load_portfolio_lab_components,
    load_workbench_strategy_cards,
    load_workbench_strategy_packages,
    inspect_workbench_strategy_package,
    materialize_factory_components_as_workbench_runs,
    orb_930_backtest_payload,
    persist_workbench_run_bundle,
    portfolio_lab_component_table,
    persist_workbench_strategy_package,
    persist_portfolio_preregistration_draft,
    write_workbench_phase_report,
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

    assert {"xmom", "gaprev", "sec8k", "pead", "lowvol", "form4", "dollarbar", "orb930", "regime"}.issubset(keys)
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


def test_orb_930_payload_reads_backtest_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "experiments/provider_aware_research/execution_outputs/ORB-930-CROSS-ASSET-BACKTEST-001"
    output_dir.mkdir(parents=True)
    (output_dir / "final_decision.json").write_text(
        json.dumps({"decision": "ORB_930_ARCHIVE_CURRENT_FORM", "promotion_allowed": False, "best_configuration": {"symbol": "BTC-USD"}}),
        encoding="utf-8",
    )
    pd.DataFrame([{"symbol": "BTC-USD", "net_return": 0.01}]).to_csv(output_dir / "trades.csv", index=False)
    pd.DataFrame([{"symbol": "BTC-USD", "net_return_sum": 0.01}]).to_csv(output_dir / "summary.csv", index=False)
    (output_dir / "orb_930_report.md").write_text("# ORB report\n", encoding="utf-8")

    payload = orb_930_backtest_payload(tmp_path)

    assert payload["available"] is True
    assert payload["best"]["symbol"] == "BTC-USD"
    assert payload["by_symbol"].iloc[0]["trades"] == 1


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


def test_delisted_data_source_gate_payload_surfaces_admissible_sources() -> None:
    payload = delisted_data_source_gate_payload()

    assert payload["manifest"]["current_candidate_status"] == "PROXY_INVESTMENT_CANDIDATE_ONLY"
    assert {"CRSP", "Norgate Data", "Sharadar/Nasdaq Data Link"}.issubset(set(payload["admissible_sources"]))
    assert not payload["candidate_source_matrix"].empty
    assert not payload["unlock_requirements"].empty


def test_workbench_universe_catalogs_are_much_larger_than_local_price_coverage() -> None:
    large = build_workbench_manifest(
        name="Large catalog",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )
    small = build_workbench_manifest(
        name="Small catalog",
        template="Momentum",
        universe="small-cap active-only exploratory sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )

    large_scope = build_workbench_data_scope_preview(large)
    small_scope = build_workbench_data_scope_preview(small)

    assert len(WORKBENCH_CONFIGURED_LARGECAP_SYMBOLS) >= 100
    assert len(WORKBENCH_CONFIGURED_SMALLCAP_SYMBOLS) >= 100
    assert large_scope["configured_symbols"] >= 100
    assert small_scope["configured_symbols"] >= 100
    assert large_scope["local_price_symbols"] <= large_scope["configured_symbols"]
    assert small_scope["local_price_symbols"] <= small_scope["configured_symbols"]


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


def test_workbench_templates_use_distinct_local_rule_profiles() -> None:
    previews = []
    for template in WORKBENCH_TEMPLATES:
        manifest = build_workbench_manifest(
            name=f"{template} local dry-run",
            template=template,
            universe="expanded local research sandbox",
            holding_period_days=21,
            cost_bps=500,
            allow_provider_query=True,
        )
        previews.append(build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest)))

    profiles = {preview["local_data_summary"]["template_rule_profile"] for preview in previews}
    result_shapes = {
        (
            preview["template"],
            preview["local_data_summary"]["template_rule_profile"],
            preview["simulated_trades"],
            preview["gross_edge_proxy"],
            preview["cost_breakdown"]["net_return_sum"],
        )
        for preview in previews
    }

    assert profiles == {
        template if template != "Custom Rule Builder" else "Custom Rule Builder:momentum_21d:top:none:holding_period"
        for template in WORKBENCH_TEMPLATES
    }
    assert len(result_shapes) == len(WORKBENCH_TEMPLATES)


def test_custom_rule_builder_manifest_changes_local_rule_profile_and_results() -> None:
    momentum = build_workbench_manifest(
        name="Momentum baseline",
        template="Momentum",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=500,
        allow_provider_query=False,
    )
    custom = build_workbench_manifest(
        name="My custom dip rule",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=500,
        allow_provider_query=False,
        custom_rules={
            "signal": "dip_2d",
            "selection": "bottom",
            "entries_per_symbol": 12,
            "allowed_symbols": "CABA,CRMD,IOVA,SPY",
            "market_filter": "volume_above_20d",
            "exit_policy": "risk_box",
            "stop_loss_pct": 12,
            "take_profit_pct": 25,
        },
    )

    momentum_preview = build_controlled_backtest_preview(momentum, validate_workbench_manifest(momentum))
    custom_preview = build_controlled_backtest_preview(custom, validate_workbench_manifest(custom))

    assert custom["custom_rules"]["signal"] == "dip_2d"
    assert custom["custom_rules"]["market_filter"] == "volume_above_20d"
    assert custom["custom_rules"]["exit_policy"] == "risk_box"
    assert custom["custom_rules"]["stop_loss_pct"] == 12
    assert custom["custom_rules"]["take_profit_pct"] == 25
    assert "risk_box" in custom_preview["local_data_summary"]["template_rule_profile"]
    assert custom_preview["local_data_summary"]["custom_allowed_symbols"] == ["CABA", "CRMD", "IOVA", "SPY"]
    assert all(row["exit_reason"] in {"holding_period", "stop_loss", "take_profit"} for row in custom_preview["trade_rows"])
    assert custom_preview["simulated_trades"] != momentum_preview["simulated_trades"]
    assert custom_preview["cost_breakdown"]["net_return_sum"] != momentum_preview["cost_breakdown"]["net_return_sum"]


def test_workbench_strategy_narrative_explains_custom_rule_and_data_coverage() -> None:
    manifest = build_workbench_manifest(
        name="Readable custom volume shock",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=30,
        cost_bps=375,
        allow_provider_query=False,
        custom_rules={
            "signal": "volume_shock",
            "selection": "top",
            "entries_per_symbol": 20,
            "allowed_symbols": "CABA, CRMD, IOVA",
            "market_filter": "positive_5d",
            "exit_policy": "risk_box",
            "stop_loss_pct": 10,
            "take_profit_pct": 30,
        },
    )
    scope = build_workbench_data_scope_preview(manifest)

    narrative = build_workbench_strategy_narrative(manifest, scope)

    assert narrative["plain_english_rule"].startswith("Buy")
    assert "volume shock" in narrative["plain_english_rule"].lower()
    assert "positive 5-day trend filter" in narrative["plain_english_rule"].lower()
    assert "10%" in narrative["exit_plain_english"]
    assert "30%" in narrative["exit_plain_english"]
    assert "30" in narrative["exit_plain_english"]
    assert narrative["data_coverage"]["configured_symbols"] >= 100
    assert narrative["data_coverage"]["local_price_symbols"] == 3
    assert any("No provider query" in item for item in narrative["guardrails"])


def test_workbench_visual_diagnostics_exposes_distribution_and_top_winners() -> None:
    manifest = build_workbench_manifest(
        name="Visual diagnostics",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=500,
        allow_provider_query=False,
        custom_rules={
            "signal": "momentum_5d",
            "selection": "top",
            "entries_per_symbol": 15,
            "allowed_symbols": "CABA,CRMD,IOVA,SPY",
        },
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    diagnostics = build_workbench_visual_diagnostics(preview)

    assert diagnostics["trade_distribution"]
    assert diagnostics["top_winners"]
    assert diagnostics["equity_curve"]
    assert {"bucket", "trade_count"}.issubset(diagnostics["trade_distribution"][0])
    assert {"symbol", "net_return", "share_of_positive_net"}.issubset(diagnostics["top_winners"][0])
    assert diagnostics["verdict_blocks"]
    assert diagnostics["result_explainer"]["headline"] == preview["automatic_verdict"]["decision"]


def test_workbench_result_summary_explains_outcome_in_plain_language() -> None:
    manifest = build_workbench_manifest(
        name="Plain result",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=500,
        allow_provider_query=False,
        custom_rules={"signal": "momentum_5d", "selection": "top", "entries_per_symbol": 10},
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    summary = build_workbench_result_summary(preview)

    assert {"headline", "plain_result", "primary_blocker", "next_best_action"}.issubset(summary)
    assert "Promotion remains locked" in summary["plain_result"]
    assert summary["net_return_percent"].endswith("%")


def test_display_safe_records_serializes_nested_table_values() -> None:
    records = [
        {"gate": "outlier", "value": {"net_sum": 1.2, "ex_top3": -0.4}, "count": 5},
        {"gate": "median", "value": 0.2, "count": 5},
    ]

    safe = display_safe_records(records)

    assert safe[0]["value"] == '{"ex_top3": -0.4, "net_sum": 1.2}'
    assert safe[1]["value"] == "0.2"
    assert safe[0]["count"] == "5"


def test_workbench_auto_switches_long_holding_to_investment_mode() -> None:
    manifest = build_workbench_manifest(
        name="PDUFA convex basket",
        template="PDUFA Run-Up",
        universe="expanded local research sandbox",
        holding_period_days=180,
        cost_bps=500,
        allow_provider_query=True,
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    assert manifest["requested_mode"] == "Auto"
    assert manifest["analysis_mode"] == "Investment"
    assert preview["analysis_mode"] == "Investment"
    assert preview["portfolio_diagnostics"]["holding_period_days"] == 180
    assert preview["portfolio_diagnostics"]["total_net_return"] == preview["cost_breakdown"]["net_return_sum"]
    assert "convex" in preview["why"].lower()
    assert "portfolio_diagnostics" in preview["dry_run_rows"][-1]["metric"]


def test_investment_mode_does_not_reject_only_because_trade_median_or_win_rate_is_weak() -> None:
    manifest = build_workbench_manifest(
        name="Forced investment reading",
        template="PDUFA Run-Up",
        universe="expanded local research sandbox",
        holding_period_days=180,
        cost_bps=500,
        allow_provider_query=True,
        strategy_mode="Investment",
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    assert preview["analysis_mode"] == "Investment"
    assert preview["robustness_panel"]["median_return_gate"]["status"] in {"INFO", "PASS", "BLOCK"}
    assert preview["robustness_panel"]["win_rate_gate"]["status"] in {"INFO", "PASS", "BLOCK"}
    if preview["robustness_panel"]["median_return_gate"]["status"] == "BLOCK" or preview["robustness_panel"]["win_rate_gate"]["status"] == "BLOCK":
        assert preview["automatic_verdict"]["decision"] != "REJECTED_WEAK_DISTRIBUTION"
    assert "investment" in preview["automatic_verdict"]["summary"].lower()


def test_event_investment_proxy_flags_high_survivorship_bias() -> None:
    manifest = build_workbench_manifest(
        name="PDUFA proxy bias warning",
        template="PDUFA Run-Up",
        universe="expanded local research sandbox",
        holding_period_days=180,
        cost_bps=500,
        allow_provider_query=True,
        strategy_mode="Investment",
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    warnings = preview["bias_warnings"]
    warning_ids = {warning["warning_id"] for warning in warnings}
    assert "SURVIVORSHIP_BIAS_SUSPECTED_HIGH" in warning_ids
    assert "PROXY_INVESTMENT_CANDIDATE_ONLY" in preview["automatic_verdict"]["summary"]
    assert "SURVIVORSHIP_BIAS_SUSPECTED_HIGH" in preview["markdown_report"]


def test_strategy_factory_generates_uncreated_template_variants() -> None:
    components = build_strategy_factory_components(max_variants=24)

    assert components
    assert all(component["source"] == "factory_generated" for component in components)
    assert all("factory_manifest" in component for component in components)
    assert all("factory_preview" in component for component in components)
    assert any("FACTORY" in component["component_id"] for component in components)
    assert any(component["template"] == "PDUFA Run-Up" for component in components)
    assert all(component["provider_query_performed"] is False for component in components)
    assert any(component["trade_count"] > 0 for component in components)


def test_materialize_factory_components_keeps_factory_provenance(tmp_path: Path) -> None:
    components = build_strategy_factory_components(max_variants=12)
    selected_ids = [component["component_id"] for component in components[:3]]

    result = materialize_factory_components_as_workbench_runs(components, selected_ids, root=tmp_path)

    assert result["materialized_count"] == 3
    assert result["skipped_count"] == 0
    for bundle in result["bundles"]:
        assert Path(bundle["manifest_path"]).exists()
        dry_run = json.loads(Path(bundle["result_path"]).read_text(encoding="utf-8"))
        warning_ids = {warning["warning_id"] for warning in dry_run["bias_warnings"]}
        assert "FACTORY_GENERATED_NOT_PREREGISTERED" in warning_ids
        assert "FACTORY_SELECTED_AFTER_SEARCH_NOT_PROMOTABLE" in warning_ids

    saved = load_portfolio_lab_components(root=tmp_path, limit=10)
    assert len(saved) == 3
    assert all("FACTORY_SELECTED_AFTER_SEARCH_NOT_PROMOTABLE" in component["bias_warnings"] for component in saved)


def test_portfolio_preregistration_draft_preserves_overfit_disclosure(tmp_path: Path) -> None:
    components = build_strategy_factory_components(max_variants=24)
    selected_ids = [component["component_id"] for component in components[:3]]
    draft = build_portfolio_preregistration_draft(
        components,
        selected_ids,
        source_search={"selection_rule": "predeclared_robust_score_no_promotion", "evaluated_candidate_count": 42},
    )

    assert draft["status"] == "PREREGISTRATION_DRAFT_REQUIRES_MANUAL_APPROVAL"
    assert draft["promotion_allowed"] is False
    assert draft["paper_trading_allowed"] is False
    assert draft["live_trading_allowed"] is False
    assert draft["source_search"]["evaluated_candidate_count"] == 42
    assert len(draft["selected_components"]) == 3
    assert "selected_after_search" in draft["anti_overfit_disclosures"]
    assert "factory_generated_scope" in draft["anti_overfit_disclosures"]
    assert draft["falsification_criteria"]

    paths = persist_portfolio_preregistration_draft(draft, root=tmp_path)

    assert Path(paths["json_path"]).exists()
    assert Path(paths["markdown_path"]).exists()
    loaded = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))
    assert loaded["draft_id"] == draft["draft_id"]
    assert "manual approval" in Path(paths["markdown_path"]).read_text(encoding="utf-8").lower()


def test_portfolio_preregistration_draft_keeps_factory_scope_after_materialization() -> None:
    components = [
        {
            "component_id": "abc123",
            "strategy_name": "Materialized Factory Momentum 180d 100bps",
            "template": "Momentum",
            "analysis_mode": "Investment",
            "decision": "FACTORY_MATERIALIZED_DIAGNOSTIC_ONLY",
            "source": "factory_materialized",
            "trade_count": 10,
            "net_return_sum": 1.2,
            "cost_bps": 100,
            "bias_warnings": ["FACTORY_SELECTED_AFTER_SEARCH_NOT_PROMOTABLE"],
        }
    ]

    draft = build_portfolio_preregistration_draft(components, ["abc123"])

    assert draft["source_summary"]["factory_materialized"] == 1
    assert "factory_generated_scope" in draft["anti_overfit_disclosures"]


def test_portfolio_preview_can_include_factory_generated_components(tmp_path: Path) -> None:
    preview = build_portfolio_lab_preview(root=tmp_path, include_factory_generated=True, factory_variant_limit=12)

    assert preview["summary"]["component_count"] >= 3
    assert preview["component_source_summary"]["factory_generated"] >= 3
    assert preview["portfolio_search"]["search_performed"] is True
    assert preview["final_decision"]["promotion_allowed"] is False


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


def test_load_workbench_strategy_cards_reads_saved_runs(tmp_path: Path) -> None:
    manifest = build_workbench_manifest(
        name="Saved strategy",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=5,
        cost_bps=100,
        allow_provider_query=False,
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)
    persist_workbench_run_bundle(manifest, validation, preview, root=tmp_path)

    cards = load_workbench_strategy_cards(root=tmp_path)

    assert len(cards) == 1
    assert cards[0]["strategy_name"] == "Saved strategy"
    assert cards[0]["template"] == "Momentum"
    assert cards[0]["artifact_dir"]
    assert cards[0]["net_return_sum"] == preview["cost_breakdown"]["net_return_sum"]


def test_workbench_comparison_table_ranks_saved_runs_by_net_return() -> None:
    cards = [
        {"strategy_name": "Weak", "template": "Momentum", "decision": "REJECTED", "simulated_trades": 30, "net_return_sum": -0.2, "artifact_dir": "a"},
        {"strategy_name": "Strong", "template": "Custom", "decision": "CANDIDATE", "simulated_trades": 40, "net_return_sum": 0.35, "artifact_dir": "b"},
    ]

    table = build_workbench_comparison_table(cards)

    assert list(table["strategy_name"]) == ["Strong", "Weak"]
    assert list(table["net_return_percent"]) == [35.0, -20.0]
    assert "Promotion locked" in table.iloc[0]["governance_note"]


def test_workbench_backtest_readiness_maps_dry_run_to_real_backtest_steps() -> None:
    manifest = build_workbench_manifest(
        name="Readiness map",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=300,
        allow_provider_query=False,
        custom_rules={"signal": "momentum_5d", "selection": "top", "entries_per_symbol": 8},
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)

    readiness = build_workbench_backtest_readiness(manifest, validation, preview)

    assert readiness["overall_status"] in {"DRY_RUN_READY_REAL_BACKTEST_LOCKED", "REAL_BACKTEST_PREP_REQUIRED"}
    assert readiness["promotion_allowed"] is False
    assert readiness["stages"][0]["stage"] == "Manifest"
    assert any(stage["stage"] == "Provider/data contract" for stage in readiness["stages"])
    assert readiness["next_user_action"]


def test_workbench_strategy_blueprint_and_glossary_are_user_readable() -> None:
    manifest = build_workbench_manifest(
        name="Blueprint strategy",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=45,
        cost_bps=375,
        allow_provider_query=False,
        strategy_mode="Investment",
        custom_rules={
            "signal": "volume_shock",
            "selection": "top",
            "entries_per_symbol": 12,
            "market_filter": "positive_5d",
            "exit_policy": "risk_box",
            "stop_loss_pct": 12,
            "take_profit_pct": 40,
        },
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest))

    blueprint = build_workbench_strategy_blueprint(manifest, preview)
    glossary = build_workbench_metric_glossary(preview)

    assert blueprint["strategy_name"] == "Blueprint strategy"
    assert "what_the_user_built" in blueprint
    assert "real_backtest_unlock" in blueprint
    assert any(item["metric"] == "Net return sum" for item in glossary)
    assert all(item["plain_meaning"] for item in glossary)


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


def test_workbench_rule_flow_exposes_composable_strategy_blocks() -> None:
    manifest = build_workbench_manifest(
        name="Flow strategy",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=20,
        cost_bps=250,
        allow_provider_query=False,
        custom_rules={
            "signal": "volume_shock",
            "selection": "top",
            "entries_per_symbol": 10,
            "market_filter": "positive_5d",
            "exit_policy": "risk_box",
            "stop_loss_pct": 10,
            "take_profit_pct": 35,
        },
    )

    flow = build_workbench_rule_flow(manifest)

    assert [item["block"] for item in flow] == ["Universe", "Signal", "Filter", "Entry", "Risk", "Exit", "Gates"]
    assert any("volume shock" in item["description"].lower() for item in flow)
    assert any("10%" in item["description"] for item in flow)


def test_workbench_trade_annotation_story_marks_entry_exit_and_risk_box(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    rows = []
    for offset in range(12):
        rows.append(
            {
                "symbol": "AAA",
                "date": f"2026-01-{offset + 1:02d}",
                "open": 10 + offset * 0.2,
                "high": 10.5 + offset * 0.2,
                "low": 9.8 + offset * 0.2,
                "close": 10 + offset * 0.2,
                "volume": 1000 + offset * 20,
            }
        )
    pd.DataFrame(rows).to_csv(prices, index=False)
    manifest = build_workbench_manifest(
        name="Annotated trade",
        template="Custom Rule Builder",
        universe="local archived Databento panel",
        holding_period_days=4,
        cost_bps=50,
        allow_provider_query=False,
        custom_rules={
            "signal": "momentum_5d",
            "selection": "top",
            "entries_per_symbol": 3,
            "exit_policy": "risk_box",
            "stop_loss_pct": 8,
            "take_profit_pct": 20,
        },
    )
    preview = build_controlled_backtest_preview(manifest, validate_workbench_manifest(manifest), price_file=prices)

    story = build_workbench_trade_annotation_story(manifest, preview, price_file=prices)

    assert story["available"] is True
    assert story["symbol"] == "AAA"
    assert {marker["kind"] for marker in story["markers"]} >= {"entry", "exit"}
    assert story["risk_box"]["stop_price"] > 0
    assert story["risk_box"]["take_profit_price"] > story["risk_box"]["entry_price"]


def test_write_workbench_phase_report_records_v2_progress(tmp_path: Path) -> None:
    path = write_workbench_phase_report(root=tmp_path)

    text = path.read_text(encoding="utf-8")
    assert "Strategy Workbench V2" in text
    assert "Strategy Workbench V3" in text
    assert "Chart Annotator" in text
    assert "strategy package" in text.lower()
    assert "promotion_allowed" in text


def test_workbench_strategy_package_contains_governed_backtest_files() -> None:
    manifest = build_workbench_manifest(
        name="Package strategy",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=30,
        cost_bps=300,
        allow_provider_query=False,
        custom_rules={"signal": "momentum_5d", "selection": "top", "entries_per_symbol": 6},
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)

    package = build_workbench_strategy_package(manifest, validation, preview)

    assert set(package) == {
        "strategy_manifest.json",
        "pre_run_gate.json",
        "data_contract.json",
        "command_spec.json",
        "risk_policy.json",
        "README.md",
        "dry_run_report.md",
    }
    assert package["pre_run_gate.json"]["promotion_allowed"] is False
    assert package["data_contract.json"]["provider_query_allowed"] is False
    assert package["command_spec.json"]["execution_allowed"] is False
    assert "--live" in package["command_spec.json"]["forbidden_flags"]
    assert "Package strategy" in package["README.md"]


def test_persist_workbench_strategy_package_writes_all_files(tmp_path: Path) -> None:
    manifest = build_workbench_manifest(
        name="Persist package",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)

    bundle = persist_workbench_strategy_package(manifest, validation, preview, root=tmp_path)

    assert Path(bundle["package_dir"]).exists()
    for filename in [
        "strategy_manifest.json",
        "pre_run_gate.json",
        "data_contract.json",
        "command_spec.json",
        "risk_policy.json",
        "README.md",
        "dry_run_report.md",
    ]:
        assert Path(bundle["files"][filename]).exists()
    assert "strategy_package" in bundle["package_dir"]


def test_load_and_inspect_workbench_strategy_packages(tmp_path: Path) -> None:
    manifest = build_workbench_manifest(
        name="Inspectable package",
        template="Momentum",
        universe="large-cap / ETF clean-data sandbox",
        holding_period_days=21,
        cost_bps=250,
        allow_provider_query=False,
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)
    bundle = persist_workbench_strategy_package(manifest, validation, preview, root=tmp_path)

    packages = load_workbench_strategy_packages(root=tmp_path)
    inspection = inspect_workbench_strategy_package(Path(bundle["package_dir"]))

    assert len(packages) == 1
    assert packages[0]["strategy_name"] == "Inspectable package"
    assert packages[0]["status"] == "READY_FOR_RUNNER_BUILD"
    assert packages[0]["execution_allowed"] is False
    assert inspection["package_dir"] == bundle["package_dir"]
    assert inspection["status"] == "READY_FOR_RUNNER_BUILD"
    assert inspection["files_present"]["README.md"] is True
    assert inspection["readiness_rows"][0]["check"] == "execution_allowed"
    assert inspection["readme"].startswith("# Strategy Package")
    assert inspection["runner_available"] is False
    assert inspection["runner_output_dir"].endswith("diagnostic_runner")


def test_portfolio_lab_helpers_compose_saved_workbench_runs(tmp_path: Path) -> None:
    for name, template in [
        ("Portfolio momentum", "Momentum"),
        ("Portfolio reversion", "Mean Reversion"),
        ("Portfolio custom", "Custom Rule Builder"),
    ]:
        manifest = build_workbench_manifest(
            name=name,
            template=template,
            universe="large-cap / ETF clean-data sandbox",
            holding_period_days=21,
            cost_bps=250,
            allow_provider_query=False,
            custom_rules={"signal": "momentum_5d", "selection": "top", "entries_per_symbol": 3},
        )
        validation = validate_workbench_manifest(manifest)
        preview = build_controlled_backtest_preview(manifest, validation)
        persist_workbench_run_bundle(manifest, validation, preview, root=tmp_path)

    components = load_portfolio_lab_components(root=tmp_path)
    component_table = portfolio_lab_component_table(components)
    portfolio = build_portfolio_lab_preview([component["component_id"] for component in components], root=tmp_path, policy="equal_weight")

    assert len(components) == 3
    assert set(["strategy", "template", "decision", "trades"]).issubset(component_table.columns)
    assert portfolio["final_decision"]["promotion_allowed"] is False
    assert portfolio["summary"]["component_count"] == 3
    assert portfolio["allocation"]
    assert portfolio["gate_panel"]
