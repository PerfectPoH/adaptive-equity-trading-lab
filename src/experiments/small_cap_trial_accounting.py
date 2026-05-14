from __future__ import annotations

from typing import Any


def build_rankex_trial_001_accounting() -> dict[str, Any]:
    return {
        "trial_id": "TRIAL-RANKEX-001",
        "research_question": "ranking_intra_candidate",
        "hypothesis_family": "ranking",
        "status": "implementation_ready_not_run",
        "train_or_design_window": "2022-01-03..2023-12-29",
        "validation_window": "2024-01-02..2024-12-31",
        "oos_window": "2025-01-02..2025-12-29",
        "universe_definition": "same eligible 30-name small-cap metadata subset used by corrected archived validation unless explicitly superseded by a new pre-registered universe file",
        "baseline_run_id": "small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_risk_sizing_20260512",
        "candidate_run_id": None,
        "benchmark_set": [
            "cash_flat",
            "iwm_proxy",
            "equal_weight_universe",
            "random_entry_baseline",
            "ticker_holding_window",
            "archived_setup_corrected_risk_sizing",
        ],
        "ranking_policy": {
            "rank_column": "small_cap_scanner_score",
            "ascending": False,
            "tie_breakers": [
                {"column": "relative_volume_20d", "ascending": False},
                {"column": "open_to_close_return", "ascending": False},
                {"column": "symbol", "ascending": True},
            ],
        },
        "ex_top_n_results_required": [1, 3],
        "decision_rule": "candidate may only advance if validation beats ticker_holding_window and random_entry_baseline, remains positive excluding top1 and top3 trades, shows no single-year/regime dependency, keeps insufficient_funds near zero without increasing risk_fraction, and then passes the pre-declared 2025 OOS window",
        "notes_on_multiple_testing": "first ranking/exits trial after archive decision; no parameter sweep or additional ranking family is authorized by this preregistration",
    }
