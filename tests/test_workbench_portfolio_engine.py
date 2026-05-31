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
    assert matrix.loc["2026-01-03", "bbb222"] == 0.0
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
        "portfolio_gate_panel_path",
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
