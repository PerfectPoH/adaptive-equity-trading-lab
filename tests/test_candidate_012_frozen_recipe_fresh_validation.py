import json
from pathlib import Path

import pytest

from src.experiments.candidate_012_frozen_recipe_fresh_validation import (
    build_candidate_012_fresh_validation_spec,
    persist_candidate_012_fresh_validation_spec,
    validate_candidate_012_fresh_validation_spec,
)


def _candidate_011_result(tmp_path: Path) -> Path:
    result = {
        "run_id": "CANDIDATE-011-RISK-OFF-MEAN-REVERSION-001",
        "linked_dataset": "experiments/provider_aware_research/data_inputs/CANDIDATE-007-NORGATE-DATASET-RERUN-002",
        "strategy_contract": {
            "strategy_id": "CANDIDATE-011-RISK-OFF-MEAN-REVERSION-BREADTH",
            "rebalance_every_n_trading_days": 20,
            "cost_bps_round_trip": 500,
            "allowed_regimes": ["RISK_OFF"],
            "tradability": {
                "min_history_rows": 90,
                "min_price_asof": 1.0,
                "min_trailing_20d_median_turnover": 1000000.0,
            },
            "sleeve": {
                "name": "risk_off_mean_reversion_5d",
                "lookback_days": 5,
                "holding_days": 10,
                "top_k": 20,
                "rank_direction": "lowest_return",
            },
        },
        "summary_by_split": {
            "oos": {
                "trade_count": 19,
                "weighted_net_sum": 0.06586794899032468,
                "median_net_return": 0.04353333624035231,
                "win_rate": 0.7368421052631579,
            }
        },
        "robustness": {"oos_ex_top3_weighted_net_sum": 0.011322359249125807},
        "final_decision": {"decision": "CANDIDATE_011_RISK_OFF_MEAN_REVERSION_ARCHIVE_NO_PROMOTION"},
    }
    path = tmp_path / "candidate_011_result.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    return path


def test_candidate_012_spec_freezes_candidate_011_recipe_and_forbids_discovery_dataset(tmp_path: Path) -> None:
    source = _candidate_011_result(tmp_path)

    spec = build_candidate_012_fresh_validation_spec(candidate_011_result_path=source)

    assert spec["status"] == "FROZEN_RECIPE_AWAITING_FRESH_DATA"
    assert spec["frozen_recipe"]["sleeve"]["lookback_days"] == 5
    assert spec["frozen_recipe"]["sleeve"]["holding_days"] == 10
    assert spec["frozen_recipe"]["sleeve"]["top_k"] == 20
    assert spec["fresh_data_contract"]["forbidden_dataset_paths"] == [
        "experiments/provider_aware_research/data_inputs/CANDIDATE-007-NORGATE-DATASET-RERUN-002"
    ]
    assert spec["execution_permissions"]["backtest_allowed_now"] is False
    assert spec["execution_permissions"]["parameter_sweep_allowed"] is False
    assert spec["execution_permissions"]["promotion_allowed"] is False


def test_candidate_012_validator_blocks_same_dataset_and_allows_fresh_path(tmp_path: Path) -> None:
    source = _candidate_011_result(tmp_path)
    spec = build_candidate_012_fresh_validation_spec(candidate_011_result_path=source)

    blocked = validate_candidate_012_fresh_validation_spec(
        spec,
        proposed_dataset_path="experiments/provider_aware_research/data_inputs/CANDIDATE-007-NORGATE-DATASET-RERUN-002",
    )
    allowed = validate_candidate_012_fresh_validation_spec(
        spec,
        proposed_dataset_path="experiments/provider_aware_research/data_inputs/CANDIDATE-012-FRESH-DATASET-PLACEHOLDER",
    )

    assert blocked["status"] == "BLOCKED"
    assert "same_dataset_as_discovery_forbidden" in blocked["blockers"]
    assert allowed["status"] == "READY_FOR_SEPARATE_DATA_GATE"
    assert allowed["backtest_allowed_now"] is False


def test_candidate_012_persistence_writes_audit_artifacts(tmp_path: Path) -> None:
    source = _candidate_011_result(tmp_path)
    spec = build_candidate_012_fresh_validation_spec(candidate_011_result_path=source)

    paths = persist_candidate_012_fresh_validation_spec(spec, root=tmp_path)

    assert (paths["artifact_dir"] / "fresh_validation_spec.json").exists()
    assert (paths["artifact_dir"] / "fresh_validation_report.md").exists()
    assert (paths["artifact_dir"] / "final_decision.json").exists()


def test_candidate_012_builder_refuses_mutated_source_recipe(tmp_path: Path) -> None:
    source = _candidate_011_result(tmp_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["strategy_contract"]["sleeve"]["top_k"] = 19
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match="Candidate 011 recipe is not the frozen recipe"):
        build_candidate_012_fresh_validation_spec(candidate_011_result_path=source)
