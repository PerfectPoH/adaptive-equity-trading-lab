from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "CANDIDATE-012-FROZEN-RECIPE-FRESH-VALIDATION-SPEC-001"
SOURCE_RESULT = Path(
    "experiments/provider_aware_research/execution_outputs/"
    "CANDIDATE-011-RISK-OFF-MEAN-REVERSION-001/candidate_011_risk_off_mean_reversion_result.json"
)
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
FROZEN_RECIPE = {
    "strategy_id": "CANDIDATE-012-FROZEN-RISK-OFF-MEAN-REVERSION-5D",
    "source_strategy_id": "CANDIDATE-011-RISK-OFF-MEAN-REVERSION-BREADTH",
    "rebalance_every_n_trading_days": 20,
    "cost_bps_round_trip": 500,
    "allowed_regimes": ["RISK_OFF"],
    "tradability": {
        "min_history_rows": 90,
        "min_price_asof": 1.0,
        "min_trailing_20d_median_turnover": 1_000_000.0,
    },
    "sleeve": {
        "name": "risk_off_mean_reversion_5d",
        "lookback_days": 5,
        "holding_days": 10,
        "top_k": 20,
        "rank_direction": "lowest_return",
    },
}


def build_candidate_012_fresh_validation_spec(
    *,
    candidate_011_result_path: Path = SOURCE_RESULT,
) -> dict[str, Any]:
    source = _read_json(candidate_011_result_path)
    _validate_source_recipe(source)
    discovery_dataset = str(source["linked_dataset"]).replace("\\", "/")
    return {
        "spec_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN_RECIPE_AWAITING_FRESH_DATA",
        "purpose": (
            "Freeze the Candidate 011 RISK_OFF mean-reversion recipe and require a separate fresh-data "
            "gate before any additional backtest. This prevents sculpting Candidate 007 after discovery."
        ),
        "source_candidate": {
            "run_id": source.get("run_id"),
            "result_path": str(candidate_011_result_path),
            "decision": source.get("decision"),
            "discovery_dataset": discovery_dataset,
            "observed_oos": source.get("summary_by_split", {}).get("oos", {}),
            "observed_robustness": source.get("robustness", {}),
        },
        "frozen_recipe": deepcopy(FROZEN_RECIPE),
        "fresh_data_contract": {
            "required_status": "separate_data_gate_committed_before_backtest",
            "minimum_history_years": 5,
            "must_include_delisted": True,
            "must_include_active": True,
            "must_include_spy_iwm_benchmarks": True,
            "must_be_survivorship_aware": True,
            "must_use_adjusted_daily_ohlcv": True,
            "must_document_listing_dates": True,
            "must_document_corporate_action_policy": True,
            "forbidden_dataset_paths": [discovery_dataset],
            "allowed_dataset_examples": [
                "new Norgate full-history export outside the trial-limited Candidate 007 window",
                "CRSP/WRDS survivorship-free daily equity extract",
                "Sharadar/Nasdaq Data Link equity prices plus delisted coverage if licensing permits",
            ],
        },
        "validation_contract": {
            "time_split": "fresh dataset must define train/validation/test before execution",
            "no_recipe_search_on_test": True,
            "no_parameter_changes": True,
            "no_symbol_pruning_after_results": True,
            "cash_is_allowed_when_regime_not_risk_off": True,
            "benchmarks": ["cash", "SPY", "IWM", "equal_weight_tradable_universe"],
            "robustness_gates": {
                "min_oos_trades": 30,
                "require_positive_oos_net": True,
                "require_positive_oos_median": True,
                "require_oos_win_rate_at_least": 0.5,
                "require_positive_ex_top3_oos_net": True,
                "require_positive_ex_top10pct_oos_net": True,
                "require_oos_beats_cash": True,
                "require_oos_beats_spy": True,
                "require_oos_beats_iwm": True,
                "require_max_single_symbol_contribution_below": 0.25,
            },
        },
        "execution_permissions": {
            "backtest_allowed_now": False,
            "provider_query_allowed": False,
            "market_data_download_allowed": False,
            "parameter_sweep_allowed": False,
            "promotion_allowed": False,
            "paper_trading_allowed": False,
            "live_trading_allowed": False,
            "next_allowed_action": "create_separate_fresh_data_gate_or_wait_for_data",
        },
        "final_decision": {
            "decision": "CANDIDATE_012_FROZEN_RECIPE_AWAITING_FRESH_DATA",
            "promotion_allowed": False,
            "blockers": [
                "fresh_data_gate_required_before_backtest",
                "same_dataset_reuse_forbidden",
                "trial_limited_discovery_not_promotable",
            ],
        },
    }


def validate_candidate_012_fresh_validation_spec(spec: dict[str, Any], *, proposed_dataset_path: str) -> dict[str, Any]:
    normalized = proposed_dataset_path.replace("\\", "/")
    blockers: list[str] = []
    if normalized in spec["fresh_data_contract"]["forbidden_dataset_paths"]:
        blockers.append("same_dataset_as_discovery_forbidden")
    if spec["execution_permissions"]["backtest_allowed_now"]:
        blockers.append("spec_unexpectedly_allows_backtest_now")
    if spec["execution_permissions"]["parameter_sweep_allowed"]:
        blockers.append("spec_unexpectedly_allows_parameter_sweep")
    return {
        "status": "BLOCKED" if blockers else "READY_FOR_SEPARATE_DATA_GATE",
        "blockers": blockers,
        "proposed_dataset_path": normalized,
        "backtest_allowed_now": False,
        "next_allowed_action": "commit_fresh_data_gate_before_backtest" if not blockers else "choose_different_fresh_dataset",
    }


def persist_candidate_012_fresh_validation_spec(
    spec: dict[str, Any],
    *,
    root: Path = OUTPUT_DIR,
) -> dict[str, Path]:
    artifact_dir = root
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(artifact_dir / "fresh_validation_spec.json", spec)
    _write_json(artifact_dir / "final_decision.json", spec["final_decision"])
    (artifact_dir / "fresh_validation_report.md").write_text(_markdown_report(spec), encoding="utf-8")
    return {
        "artifact_dir": artifact_dir,
        "spec": artifact_dir / "fresh_validation_spec.json",
        "final_decision": artifact_dir / "final_decision.json",
        "report": artifact_dir / "fresh_validation_report.md",
    }


def _validate_source_recipe(source: dict[str, Any]) -> None:
    recipe = deepcopy(source.get("strategy_contract", {}))
    expected = deepcopy(FROZEN_RECIPE)
    expected.pop("strategy_id")
    expected.pop("source_strategy_id")
    recipe_subset = {
        "rebalance_every_n_trading_days": recipe.get("rebalance_every_n_trading_days"),
        "cost_bps_round_trip": recipe.get("cost_bps_round_trip"),
        "allowed_regimes": recipe.get("allowed_regimes"),
        "tradability": recipe.get("tradability"),
        "sleeve": recipe.get("sleeve"),
    }
    if recipe_subset != expected:
        raise RuntimeError("Candidate 011 recipe is not the frozen recipe.")


def _markdown_report(spec: dict[str, Any]) -> str:
    observed = spec["source_candidate"]["observed_oos"]
    gates = spec["validation_contract"]["robustness_gates"]
    lines = [
        "# Candidate 012 Frozen Recipe Fresh Validation Spec",
        "",
        f"Decision: `{spec['final_decision']['decision']}`",
        "",
        "Candidate 011 is frozen exactly as discovered. No additional backtest is authorized until a separate fresh-data gate is committed.",
        "",
        "## Frozen Recipe",
        "",
        f"- Regime: `{spec['frozen_recipe']['allowed_regimes'][0]}`",
        f"- Sleeve: `{spec['frozen_recipe']['sleeve']['name']}`",
        f"- Lookback days: `{spec['frozen_recipe']['sleeve']['lookback_days']}`",
        f"- Holding days: `{spec['frozen_recipe']['sleeve']['holding_days']}`",
        f"- Top K: `{spec['frozen_recipe']['sleeve']['top_k']}`",
        f"- Cost bps round trip: `{spec['frozen_recipe']['cost_bps_round_trip']}`",
        "",
        "## Candidate 011 Observation",
        "",
        f"- OOS trades: `{observed.get('trade_count')}`",
        f"- OOS weighted net: `{observed.get('weighted_net_sum')}`",
        f"- OOS median net: `{observed.get('median_net_return')}`",
        f"- OOS win rate: `{observed.get('win_rate')}`",
        "",
        "## Fresh Data Requirements",
        "",
        f"- Minimum history years: `{spec['fresh_data_contract']['minimum_history_years']}`",
        f"- Must include delisted: `{spec['fresh_data_contract']['must_include_delisted']}`",
        f"- Forbidden discovery dataset: `{spec['fresh_data_contract']['forbidden_dataset_paths'][0]}`",
        "",
        "## Future Validation Gates",
        "",
        f"- Min OOS trades: `{gates['min_oos_trades']}`",
        f"- Positive ex-top3 required: `{gates['require_positive_ex_top3_oos_net']}`",
        f"- Positive ex-top10pct required: `{gates['require_positive_ex_top10pct_oos_net']}`",
        f"- Must beat SPY/IWM: `{gates['require_oos_beats_spy']}` / `{gates['require_oos_beats_iwm']}`",
        "",
        "## Blockers",
        "",
    ]
    for blocker in spec["final_decision"]["blockers"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    persist_candidate_012_fresh_validation_spec(build_candidate_012_fresh_validation_spec())
