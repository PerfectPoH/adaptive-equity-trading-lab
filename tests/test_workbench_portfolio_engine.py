from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.workbench_portfolio_engine import (
    build_component_return_matrix,
    build_portfolio_allocation,
    load_workbench_portfolio_components,
    main,
    persist_portfolio_diagnostic,
    run_portfolio_diagnostic,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _component(
    root: Path,
    signature: str,
    *,
    template: str,
    decision: str,
    returns: list[float],
    warning: str | None = None,
) -> Path:
    run_dir = root / "experiments" / "provider_aware_research" / "execution_outputs" / "USER-STRATEGY-WORKBENCH" / signature
    run_dir.mkdir(parents=True)
    _write_json(
        run_dir / "dry_run_result.json",
        {
            "strategy_name": f"Strategy {signature}",
            "template": template,
            "analysis_mode": "Trading",
            "automatic_verdict": {"decision": decision, "promotion_allowed": False, "blockers": []},
            "bias_warnings": ([{"warning_id": warning, "severity": "medium", "message": warning}] if warning else []),
            "cost_bps": 500,
            "cost_breakdown": {"net_return_sum": round(sum(returns), 6), "gross_return_sum": round(sum(returns) + 0.05 * len(returns), 6)},
            "simulated_trades": len(returns),
        },
    )
    cumulative = 0.0
    equity_rows = []
    trade_rows = []
    for index, value in enumerate(returns, start=1):
        cumulative += value
        date = f"2026-01-{index:02d}"
        equity_rows.append(
            {
                "step": index,
                "date": date,
                "symbol": "AAA",
                "cumulative_gross_return": cumulative + 0.05 * index,
                "cumulative_net_return": cumulative,
                "drawdown": min(0.0, cumulative - max(cumulative, 0.0)),
            }
        )
        trade_rows.append(
            {
                "symbol": "AAA",
                "entry_date": date,
                "exit_date": date,
                "entry_price": 10.0,
                "exit_price": 10.0 * (1.0 + value),
                "gross_return": value + 0.05,
                "cost_return": 0.05,
                "net_return": value,
                "holding_days": 1,
                "rule": template,
            }
        )
    pd.DataFrame(equity_rows).to_csv(run_dir / "equity_curve.csv", index=False)
    pd.DataFrame(trade_rows).to_csv(run_dir / "trade_list.csv", index=False)
    return run_dir


def test_load_workbench_portfolio_components_reads_saved_runs(tmp_path: Path) -> None:
    _component(tmp_path, "aaa111", template="Momentum", decision="REJECTED_OUTLIER_DEPENDENCY", returns=[0.1, -0.02])
    _component(tmp_path, "bbb222", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.05, 0.3])

    components = load_workbench_portfolio_components(root=tmp_path)

    assert [component["component_id"] for component in components] == ["bbb222", "aaa111"]
    assert components[0]["strategy_name"] == "Strategy bbb222"
    assert components[0]["promotion_allowed"] is False
    assert components[0]["trade_count"] == 2


def test_load_workbench_portfolio_components_preserves_factory_materialized_lineage(tmp_path: Path) -> None:
    _component(
        tmp_path,
        "factorylineage1",
        template="Momentum",
        decision="FACTORY_MATERIALIZED_DIAGNOSTIC_ONLY",
        returns=[0.1, 0.2],
        warning="FACTORY_SELECTED_AFTER_SEARCH_NOT_PROMOTABLE",
    )

    components = load_workbench_portfolio_components(root=tmp_path)

    assert components[0]["source"] == "factory_materialized"
    assert "FACTORY_SELECTED_AFTER_SEARCH_NOT_PROMOTABLE" in components[0]["bias_warnings"]


def test_load_workbench_portfolio_components_treats_blank_trade_file_as_empty(tmp_path: Path) -> None:
    run_dir = _component(tmp_path, "blank1", template="Momentum", decision="RESEARCH_CANDIDATE_ONLY", returns=[])
    (run_dir / "trade_list.csv").write_text("\n", encoding="utf-8")
    (run_dir / "equity_curve.csv").unlink()

    components = load_workbench_portfolio_components(root=tmp_path)
    matrix = build_component_return_matrix(components)

    assert components[0]["trade_count"] == 0
    assert matrix.empty


def test_build_component_return_matrix_aligns_component_returns(tmp_path: Path) -> None:
    _component(tmp_path, "aaa111", template="Momentum", decision="REJECTED_OUTLIER_DEPENDENCY", returns=[0.1, -0.02, 0.04])
    _component(tmp_path, "bbb222", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.03, 0.02])
    components = load_workbench_portfolio_components(root=tmp_path)

    matrix = build_component_return_matrix(components)

    assert list(matrix.columns) == ["bbb222", "aaa111"]
    assert matrix.shape == (3, 2)
    # Missing periods are now NaN, not 0.0 — a component that did not exist
    # on a given date is not the same as a component that returned 0%.
    assert pd.isna(matrix.loc["2026-01-03", "bbb222"])
    assert round(float(matrix["aaa111"].sum()), 6) == 0.12


def test_portfolio_allocation_supports_equal_inverse_vol_and_sleeves(tmp_path: Path) -> None:
    _component(tmp_path, "core01", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.02, 0.01, 0.02])
    _component(tmp_path, "conv01", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.1, 0.5, -0.05])
    _component(tmp_path, "tact01", template="9:30 AM ORB", decision="REJECTED_OUTLIER_DEPENDENCY", returns=[0.03, -0.02, 0.01])
    components = load_workbench_portfolio_components(root=tmp_path)
    matrix = build_component_return_matrix(components)

    equal = build_portfolio_allocation(components, matrix, policy="equal_weight")
    inverse = build_portfolio_allocation(components, matrix, policy="inverse_volatility", max_component_weight=0.5)
    sleeve = build_portfolio_allocation(components, matrix, policy="sleeve_allocation", max_convex_weight=0.2)

    assert round(sum(row["weight"] for row in equal), 6) == 1.0
    assert max(row["weight"] for row in inverse) <= 0.5
    assert round(sum(row["weight"] for row in sleeve), 6) == 1.0
    assert sum(row["weight"] for row in sleeve if row["sleeve"] == "convex") <= 0.2


def test_run_portfolio_diagnostic_emits_gates_and_never_promotes(tmp_path: Path) -> None:
    _component(tmp_path, "winner", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.02, 0.7, -0.01], warning="PROXY_DATA_SCOPE_NOT_PROMOTABLE")
    _component(tmp_path, "steady", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.02, 0.03, 0.01])
    _component(tmp_path, "fragile", template="9:30 AM ORB", decision="REJECTED_OUTLIER_DEPENDENCY", returns=[-0.01, 0.02, -0.02])
    components = load_workbench_portfolio_components(root=tmp_path)

    diagnostic = run_portfolio_diagnostic(components, policy="sleeve_allocation")

    assert diagnostic["final_decision"]["promotion_allowed"] is False
    assert diagnostic["final_decision"]["provider_query_performed"] is False
    assert diagnostic["summary"]["component_count"] == 3
    gate_names = {gate["gate"] for gate in diagnostic["gate_panel"]}
    assert "data_contract_gate" in gate_names
    assert "ex_best_component_gate" in gate_names
    assert "cost_stress_gate" in gate_names
    assert "correlation_gate" in gate_names
    assert diagnostic["action_plan"]
    assert diagnostic["summary"]["max_drawdown_pct"] <= 0


def test_portfolio_diagnostic_explains_high_correlation_action(tmp_path: Path) -> None:
    same_returns = [0.01, -0.02, 0.03, 0.04]
    _component(tmp_path, "one", template="Momentum", decision="RESEARCH_CANDIDATE_ONLY", returns=same_returns)
    _component(tmp_path, "two", template="Custom Rule Builder", decision="RESEARCH_CANDIDATE_ONLY", returns=same_returns)
    _component(tmp_path, "three", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.01, 0.01, -0.02, 0.02])
    _component(tmp_path, "four", template="Regime Filter", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.0, 0.01, 0.0, 0.01])
    components = load_workbench_portfolio_components(root=tmp_path)

    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    assert diagnostic["summary"]["high_correlation_pair_count"] >= 1
    assert diagnostic["high_correlation_pairs"][0]["correlation"] == 1.0
    assert any("highly correlated" in action["title"] for action in diagnostic["action_plan"])
    assert diagnostic["auto_clean"]["available"] is True
    assert len(diagnostic["auto_clean"]["removed_components"]) == 1
    assert len(diagnostic["auto_clean"]["kept_component_ids"]) == 3


def test_portfolio_diagnostic_deduplicates_same_strategy_family_before_search(tmp_path: Path) -> None:
    same_returns = [0.02, -0.01, 0.03, 0.01]
    _component(tmp_path, "dup01", template="Momentum", decision="RESEARCH_CANDIDATE_ONLY", returns=same_returns)
    _component(tmp_path, "dup02", template="Momentum", decision="RESEARCH_CANDIDATE_ONLY", returns=same_returns)
    _component(tmp_path, "mean01", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.01, 0.02, 0.01, 0.02])
    _component(tmp_path, "cat01", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.02, 0.08, -0.01, 0.04])
    components = load_workbench_portfolio_components(root=tmp_path)

    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    dedupe = diagnostic["strategy_deduplication"]
    assert dedupe["duplicate_group_count"] == 1
    assert dedupe["removed_component_count"] == 1
    assert dedupe["groups"][0]["reason"] == "same_template_and_near_identical_returns"
    assert set(dedupe["deduped_component_ids"]) == {"dup01", "mean01", "cat01"} or set(dedupe["deduped_component_ids"]) == {"dup02", "mean01", "cat01"}


def test_portfolio_diagnostic_deduplicates_same_factory_recipe_before_search() -> None:
    components = [
        {
            "component_id": "FACTORY-MOM-A",
            "strategy_name": "Factory Momentum 180d 100bps",
            "template": "Momentum",
            "analysis_mode": "Investment",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.5,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [
                {"period": "2026-01-01", "net_return": 0.20},
                {"period": "2026-01-02", "net_return": -0.10},
                {"period": "2026-01-03", "net_return": 0.30},
                {"period": "2026-01-04", "net_return": 0.10},
            ],
        },
        {
            "component_id": "FACTORY-MOM-B",
            "strategy_name": "Factory Momentum 180d 100bps",
            "template": "Momentum",
            "analysis_mode": "Investment",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.45,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [
                {"period": "2026-01-01", "net_return": -0.15},
                {"period": "2026-01-02", "net_return": 0.25},
                {"period": "2026-01-03", "net_return": -0.05},
                {"period": "2026-01-04", "net_return": 0.40},
            ],
        },
        {
            "component_id": "FACTORY-MR-A",
            "strategy_name": "Factory Mean Reversion 180d 100bps",
            "template": "Mean Reversion",
            "analysis_mode": "Investment",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.2,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [{"period": f"2026-01-0{i}", "net_return": 0.05} for i in range(1, 5)],
        },
        {
            "component_id": "FACTORY-DB-A",
            "strategy_name": "Factory Dollar-Bar Microstructure 180d 100bps",
            "template": "Dollar-Bar Microstructure",
            "analysis_mode": "Investment",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.16,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [{"period": f"2026-01-0{i}", "net_return": 0.04} for i in range(1, 5)],
        },
    ]

    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    dedupe = diagnostic["strategy_deduplication"]
    assert dedupe["duplicate_group_count"] == 1
    assert dedupe["groups"][0]["reason"] == "same_generated_strategy_recipe"
    best_ids = diagnostic["portfolio_search"]["best_basket_component_ids"]
    assert not {"FACTORY-MOM-A", "FACTORY-MOM-B"}.issubset(set(best_ids))
    labels = diagnostic["portfolio_search"]["best_component_labels"]
    assert all("FACTOR)" not in label for label in labels)
    assert any("F-" in label for label in labels)


def test_portfolio_diagnostic_searches_bounded_best_basket_without_promoting(tmp_path: Path) -> None:
    _component(tmp_path, "bad01", template="Momentum", decision="REJECTED_OUTLIER_DEPENDENCY", returns=[-0.08, -0.04, 0.01, -0.02, 0.0])
    _component(tmp_path, "good01", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.03, 0.02, -0.01, 0.04, 0.02])
    _component(tmp_path, "good02", template="Regime Filter", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.01, 0.03, 0.02, -0.01, 0.02])
    _component(tmp_path, "good03", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.02, 0.08, -0.01, 0.03, 0.02])
    components = load_workbench_portfolio_components(root=tmp_path)

    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    search = diagnostic["portfolio_search"]
    assert search["search_performed"] is True
    assert search["optimization_allowed"] is False
    assert search["selection_rule"] == "predeclared_robust_score_no_promotion"
    assert search["best_basket_component_ids"]
    assert "bad01" not in search["best_basket_component_ids"]
    assert search["best_summary"]["total_net_return"] > diagnostic["summary"]["total_net_return"]
    assert diagnostic["final_decision"]["promotion_allowed"] is False


def test_portfolio_diagnostic_blocks_factory_generated_candidate_status() -> None:
    components = [
        {
            "component_id": "FACTORY-MOM-001",
            "strategy_name": "Factory Momentum 180d 100bps",
            "template": "Momentum",
            "analysis_mode": "Trading",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.16,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [
                {"period": "2026-01-01", "net_return": 0.04},
                {"period": "2026-01-02", "net_return": 0.03},
                {"period": "2026-01-03", "net_return": 0.05},
                {"period": "2026-01-04", "net_return": 0.04},
            ],
        },
        {
            "component_id": "FACTORY-MR-001",
            "strategy_name": "Factory Mean Reversion 180d 100bps",
            "template": "Mean Reversion",
            "analysis_mode": "Trading",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.12,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [
                {"period": "2026-01-01", "net_return": 0.02},
                {"period": "2026-01-02", "net_return": 0.04},
                {"period": "2026-01-03", "net_return": 0.03},
                {"period": "2026-01-04", "net_return": 0.03},
            ],
        },
        {
            "component_id": "FACTORY-DB-001",
            "strategy_name": "Factory Dollar-Bar Microstructure 180d 100bps",
            "template": "Dollar-Bar Microstructure",
            "analysis_mode": "Trading",
            "decision": "FACTORY_GENERATED_LOCAL_DRY_RUN",
            "promotion_allowed": False,
            "bias_warnings": ["FACTORY_GENERATED_NOT_PREREGISTERED"],
            "trade_count": 4,
            "net_return_sum": 0.08,
            "cost_bps": 100,
            "source": "factory_generated",
            "inline_returns": [
                {"period": "2026-01-01", "net_return": 0.01},
                {"period": "2026-01-02", "net_return": 0.02},
                {"period": "2026-01-03", "net_return": 0.02},
                {"period": "2026-01-04", "net_return": 0.03},
            ],
        },
    ]

    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    factory_gate = next(gate for gate in diagnostic["gate_panel"] if gate["gate"] == "factory_generated_scope_gate")
    assert factory_gate["status"] == "BLOCK"
    assert diagnostic["final_decision"]["decision"] == "PORTFOLIO_FACTORY_DIAGNOSTIC_ONLY"
    assert diagnostic["final_decision"]["promotion_allowed"] is False


def test_persist_portfolio_diagnostic_writes_required_artifacts(tmp_path: Path) -> None:
    _component(tmp_path, "alpha1", template="Mean Reversion", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.02, 0.03, 0.01])
    _component(tmp_path, "alpha2", template="Momentum", decision="RESEARCH_CANDIDATE_ONLY", returns=[0.01, -0.02, 0.04])
    _component(tmp_path, "alpha3", template="PDUFA Run-Up", decision="RESEARCH_CANDIDATE_ONLY", returns=[-0.05, 0.4, -0.03])
    components = load_workbench_portfolio_components(root=tmp_path)
    diagnostic = run_portfolio_diagnostic(components, policy="equal_weight")

    paths = persist_portfolio_diagnostic(diagnostic, root=tmp_path)

    expected = {
        "portfolio_manifest_path",
        "component_manifest_path",
        "component_return_matrix_path",
        "allocation_table_path",
        "portfolio_equity_curve_path",
        "portfolio_drawdown_path",
        "portfolio_correlation_matrix_path",
        "portfolio_high_correlation_pairs_path",
        "portfolio_auto_clean_plan_path",
        "portfolio_deduplication_path",
        "portfolio_search_path",
        "portfolio_gate_panel_path",
        "portfolio_action_plan_path",
        "portfolio_final_decision_path",
        "portfolio_vault_report_path",
    }
    assert expected.issubset(paths)
    for key in expected:
        assert Path(paths[key]).exists(), key

def test_portfolio_cli_blocks_forbidden_flags(capsys) -> None:
    code = main(["--paper"])

    captured = capsys.readouterr()
    assert code == 2
    assert "forbidden_flag_present" in captured.out
